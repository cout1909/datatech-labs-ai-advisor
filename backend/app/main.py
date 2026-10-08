import asyncio
from collections import deque
from contextlib import asynccontextmanager
import json
import logging
import time
from uuid import UUID, uuid4
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from app.config import BASE_DIR, settings
from app.schemas import AnalyzeRequest, SavedAnalysis, HistoryPage, HistoryDetail
from app.database import HistoryStore
from app.services.rag_service import Retriever
from app.services import recommendation_service
from app.services.llm_service import AIUnavailable

logging.basicConfig(level=logging.INFO)

class BodyLimitMiddleware:
    def __init__(self, app, maximum=20000):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        # Bound actual streamed bytes, including requests without Content-Length.
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.maximum:
                return await JSONResponse({"detail": "Request body is too large."}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()
        await self.app(scope, replay, send)

def session_token(value, required=True):
    if not value:
        if required:
            raise HTTPException(400, 'Send your anonymous X-Session-ID token to access saved analyses.')
        return str(uuid4())
    try:
        token = UUID(value)
        if token.version != 4:
            raise ValueError('Expected random UUID')
        return str(token)
    except (ValueError, AttributeError):
        raise HTTPException(422, 'X-Session-ID must be a random UUID v4.') from None

def create_app(retriever=None, database_url=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.retriever = retriever or Retriever()
        app.state.active = 0
        app.state.requests = deque()
        app.state.history = HistoryStore(database_url or settings.database_url)
        try:
            yield
        finally:
            app.state.history.engine.dispose()

    app = FastAPI(title="DataTech Labs AI Project Advisor", version="1.1.0",
                  description="Independent demonstration project. Not affiliated with or endorsed by DataTech Labs.", lifespan=lifespan)
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Session-ID"], expose_headers=["X-Session-ID"])

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        logging.getLogger(__name__).error('Database operation failed (%s)', type(exc).__name__)
        return JSONResponse({'detail': 'History storage is temporarily unavailable. Please try again.'}, status_code=503)

    @app.get("/health")
    def health(request: Request):
        try:
            request.app.state.history.healthy()
        except SQLAlchemyError:
            raise HTTPException(503, 'History storage is unavailable.') from None
        return {"status": "ok", "llm_configured": bool(settings.groq_api_key.get_secret_value()),
                "retrieval_mode": request.app.state.retriever.mode,
                "knowledge_documents": len(request.app.state.retriever.documents), "database": "ok"}

    @app.get('/api/knowledge/status')
    def knowledge_status(request: Request):
        retriever = request.app.state.retriever
        company_count = sum(d['document_type'] == 'company_reference' for d in retriever.documents)
        return {'retrieval_mode': retriever.mode, 'documents': len(retriever.documents),
                'indexed_chunks': retriever.index.ntotal if retriever.mode == 'vector' else 0,
                'company_documents': company_count, 'general_documents': len(retriever.documents) - company_count,
                'company_identity_verified': company_count > 0,
                'scope': 'General AI engineering references; company identity pending verification.' if not company_count else 'Verified company references and labeled general engineering documents.'}

    @app.get('/api/history', response_model=HistoryPage)
    def history(request: Request, x_session_id: str | None = Header(default=None),
                limit: int = Query(default=20, ge=1, le=50), offset: int = Query(default=0, ge=0, le=10000)):
        return request.app.state.history.list(session_token(x_session_id), limit, offset)

    @app.get('/api/history/{analysis_id}', response_model=HistoryDetail)
    def history_detail(analysis_id: UUID, request: Request, x_session_id: str | None = Header(default=None)):
        record = request.app.state.history.get(session_token(x_session_id), str(analysis_id))
        if record is None:
            raise HTTPException(404, 'Analysis not found in this browser history.')
        return record

    @app.get("/api/examples")
    def examples():
        return json.loads((BASE_DIR / "app/data/examples.json").read_text(encoding="utf-8"))

    @app.post("/api/analyze", response_model=SavedAnalysis)
    async def analyze(payload: AnalyzeRequest, request: Request, response: Response, x_session_id: str | None = Header(default=None)):
        token = session_token(x_session_id, required=False)
        state = request.app.state
        now = time.monotonic()
        while state.requests and state.requests[0] <= now - 60:
            state.requests.popleft()
        # A process-wide budget protects the API key without trusting proxy IP headers.
        if len(state.requests) >= settings.rate_limit_per_minute or state.active >= settings.max_concurrent_requests:
            raise HTTPException(429, "The advisor is busy. Please try again in a minute.", headers={"Retry-After": "60"})
        state.requests.append(now)
        state.active += 1
        try:
            recommendation = await asyncio.wait_for(recommendation_service.analyze(payload, state.retriever), timeout=60)
            saved = await run_in_threadpool(state.history.save, token, payload, recommendation)
            response.headers['X-Session-ID'] = token
            return saved
        except AIUnavailable as exc:
            raise HTTPException(503, str(exc)) from None
        except TimeoutError:
            raise HTTPException(504, "Analysis timed out. Please try again.") from None
        except SQLAlchemyError:
            raise HTTPException(503, 'The recommendation could not be saved. Please try again.') from None
        except Exception as exc:
            logging.getLogger(__name__).error("Analysis failed (%s)", type(exc).__name__)
            raise HTTPException(500, "Analysis could not be completed. Please try again.") from None
        finally:
            state.active -= 1
    return app

app = create_app()
