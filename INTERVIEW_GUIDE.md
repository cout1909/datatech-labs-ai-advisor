# DataTech Labs AI Project Advisor — interview guide

Interview: **AI Full-Stack Engineer Intern, 9 October 2026, 9:00 AM IST**.

Independent demonstration project. Not affiliated with or endorsed by DataTech Labs. Current sources are general engineering references because the specific company website remains unconfirmed.

## 30-second introduction

“I built a full-stack AI project advisor that turns a business challenge into an implementation plan. React calls a FastAPI backend, which retrieves engineering references using local embeddings and FAISS, then asks Groq for a structured recommendation. Pydantic validates the output, SQLAlchemy saves it to SQLite, and users can revisit it in history. The server attaches real source metadata instead of accepting invented citations. It is an independent internship portfolio demonstration.”

## Two-minute technical explanation

“A user enters a challenge and optional industry. FastAPI validates input and applies a shared request budget. A local quantized BGE model embeds the query into 384 dimensions. FAISS searches normalized vectors built from curated reference chunks ahead of time. Relevant passages augment the Groq prompt.

“LangChain handles the provider integration. The prompt distinguishes general references from company claims and asks for the simplest suitable approach. The advisor itself uses RAG, but it can recommend forecasting, classification, OCR, or a fixed workflow rather than a chatbot. Groq strict JSON-schema mode constrains the configured model and Pydantic independently validates the result. Other models can use JSON mode with local validation. Malformed output gets one retry.

“The server constructs citations from retrieved records and saves the original problem and validated recommendation in a SQLite transaction. A random browser token scopes history. This demonstrates SQL persistence without adding registration, but it is not full user authentication.

“Tests cover API contracts, safe failures, real vector retrieval, database persistence and isolation, and browser interactions. Mocked tests are reported separately from live Groq checks. Deployment is prepared for Vercel and Render, with the explicit limitation that SQLite history on a free ephemeral filesystem can be lost.”

## Request-to-response architecture

1. React reuses a random browser token and submits `{problem, industry}` with `X-Session-ID`.
2. FastAPI checks body size, schema, shared rate budget, and concurrency.
3. BGE-small embeds the query; FAISS retrieves relevant indexed chunks.
4. Retrieved text and business input are treated as untrusted reference data.
5. LangChain calls Groq with strict schema output for the configured GPT-OSS model and a timeout.
6. Pydantic validates output; at most one schema-repair retry occurs.
7. The server attaches source URLs, document types, chunk IDs, and grounding status.
8. SQLAlchemy atomically saves UUID, problem, result JSON, UTC timestamp, token hash, and completed status.
9. FastAPI returns the saved response; React renders it and refreshes history.

## Why these choices?

**FastAPI:** Typed contracts, Swagger docs, async network calls, and TestClient. Blocking embedding and SQL work are sent to worker threads from the async analysis route.

**RAG:** External inspectable references reduce reliance on model memory and make source updates possible without retraining. Retrieval is evidence selection, not proof of every generated assertion.

**Embeddings and FAISS:** BGE-small maps text to 384 numbers. L2 normalization makes inner product equal cosine similarity. Exact IndexFlatIP search is sufficient for a tiny corpus. The 0.58 threshold is an MVP heuristic, not a probability.

**Local ONNX:** Avoids a second API key and a large PyTorch runtime. The cached model and index ship in the container. Failed vector initialization is explicitly labeled as keyword fallback.

**Groq:** `ChatGroq` reads the existing configured model/key from backend settings. The configured GPT-OSS model uses low reasoning effort, strict schema output, timeouts, and bounded retries. Other model configurations use JSON mode, which does not guarantee schema compliance.

**Pydantic:** Validates request length and output fields, list lengths, and string limits. Structural validation does not validate truth.

**SQL:** SQLAlchemy defines an analyses table; SQLite stores real records. Atomic transactions avoid partial saves. Queries paginate and filter by the anonymous token hash. Tests use isolated temporary databases, including persistence across application restarts.

**React/API communication:** Fetch sends JSON and a session header. A shared helper handles errors/timeouts. Vite proxies local requests; `VITE_API_BASE_URL` configures production. CORS permits explicit origins and required headers.

**Security/deployment:** Keys remain backend-only. Inputs never execute as SQL or shell commands. The model cannot author citation fields. Vercel hosts the static frontend and Render is configured for a Docker API. URLs are described as live only after verification. Free Render SQLite is ephemeral.

## Three-minute demo

Show the independent-demo disclaimer and general-reference scope. Generate a customer-support proposal. Explain the approach, rationale, architecture, and human oversight. Open a source and identify its chunk/type metadata. Restore a saved analysis from history and explain that only the session token is local; the record comes from SQL. Copy the result. Show `/docs`, `/api/knowledge/status`, and actual test evidence. If time allows, ask for demand forecasting to show that the app need not recommend RAG.

If live API access is unavailable, state that and demonstrate docs, index status, and tests. Do not present mocked responses as live generation.

## Challenges and improvements

- Reused the working UI/API/RAG code while changing evidence scope and adding persistence.
- The broader corpus exposed a support-retrieval gap; added a focused reference and tested unrelated queries.
- Schema correctness and factual correctness are separate; use validation plus human review.
- Production needs authentication, retention/deletion controls, durable managed SQL, migrations, backups, distributed throttling, spend controls, and monitoring.
- Expand the corpus and evaluate retrieval relevance, groundedness, abstention, and memory in the target hosting container.

## Ten likely questions

1. **RAG versus fine-tuning?** RAG adds external facts at query time; fine-tuning changes learned behavior. Transparent, updateable references fit RAG.
2. **Why FAISS?** Exact in-process search is simple for this small read-only corpus and avoids another server.
3. **What if sources are irrelevant?** Return no useful sources and explicitly label the output as a general proposal with insufficient context.
4. **How are citations protected?** Only the backend copies metadata from retrieved local records; the model does not author URLs.
5. **What if Groq fails?** Return a safe error, save no completed analysis, and never silently substitute hardcoded output.
6. **Malformed JSON?** Validate, retry once for schema repair, then return an error.
7. **Why Pydantic if structured output exists?** Local validation provides a provider-independent application contract and catches unsupported or changed behavior. Neither schema enforcement nor Pydantic establishes factual truth.
8. **How is history isolated?** A random token is a bearer capability; SQL filters by its hash. This is not production user authentication.
9. **Does SQLite persist on Render?** Not reliably on the free ephemeral filesystem. Durable hosting needs persistent storage or managed SQL.
10. **How do you prove it works?** Show actual backend/vector/SQL/build/browser test results, then a real provider request and persisted history separately when verified.
