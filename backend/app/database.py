"""SQL history, isolated by an anonymous high-entropy browser token."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from uuid import uuid4
from sqlalchemy import DateTime, String, Text, create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool
from app.schemas import AnalyzeResponse, HistoryDetail, HistoryItem, HistoryPage, SavedAnalysis

class Base(DeclarativeBase):
    pass

class Analysis(Base):
    __tablename__ = 'analyses'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_hash: Mapped[str] = mapped_column(String(64), index=True)
    problem: Mapped[str] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(50), nullable=True)
    solution_name: Mapped[str] = mapped_column(String(2000))
    recommendation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(20), default='completed')

def scope_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def item(record):
    return HistoryItem(id=record.id, problem=record.problem, industry=record.industry,
        solution_name=record.solution_name, created_at=record.created_at.replace(tzinfo=timezone.utc), status=record.status)

class HistoryStore:
    def __init__(self, url):
        parsed = make_url(url)
        if parsed.get_backend_name() != 'sqlite':
            raise ValueError('This demo supports SQLite; a hosted SQL migration needs a driver and configuration.')
        if parsed.database and parsed.database != ':memory:':
            Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
        options = {'poolclass': StaticPool} if parsed.database in (None, '', ':memory:') else {}
        self.engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 10}, **options)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def save(self, token, request, recommendation):
        record = Analysis(id=str(uuid4()), session_hash=scope_hash(token), problem=request.business_problem,
            industry=request.industry, solution_name=recommendation.solution_name,
            recommendation=recommendation.model_dump_json(), created_at=datetime.now(timezone.utc), status='completed')
        with self.sessions.begin() as session:
            session.add(record)
        return SavedAnalysis(**recommendation.model_dump(), analysis_id=record.id, created_at=record.created_at)

    def list(self, token, limit=20, offset=0):
        with self.sessions() as session:
            condition = Analysis.session_hash == scope_hash(token)
            total = session.scalar(select(func.count()).select_from(Analysis).where(condition))
            records = session.scalars(select(Analysis).where(condition).order_by(Analysis.created_at.desc(), Analysis.id).limit(limit).offset(offset)).all()
            return HistoryPage(items=[item(record) for record in records], total=total, limit=limit, offset=offset)

    def get(self, token, analysis_id):
        with self.sessions() as session:
            record = session.scalar(select(Analysis).where(Analysis.id == analysis_id, Analysis.session_hash == scope_hash(token)))
            if record is None:
                return None
            return HistoryDetail(**item(record).model_dump(), recommendation=AnalyzeResponse.model_validate_json(record.recommendation))

    def healthy(self):
        with self.engine.connect() as connection:
            connection.execute(select(1))
        return True
