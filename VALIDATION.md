# Validation evidence

Run on 8 October 2026 using the existing project `.venv` (Python 3.12.10), Node 20.17.0, and installed Chrome.

| Check | Actual result |
| --- | --- |
| Backend pytest | **31 passed**, including input/schema checks, provider failure/retry behavior, real semantic retrieval, SQL writes/reads, persistence, isolation, and CORS |
| Frontend production build | **Passed**; 1,582 modules transformed, approximately 250.5 kB JS before gzip |
| Browser suite | **6 passed**; form/examples, loading/errors, mobile layout, help, copying, history, and live integration |
| Live browser integration | **Three real Groq analyses passed**, rendered successfully and saved to SQL; saved history reopened; no browser console/page errors |
| Direct live API smoke | **Three real analyses passed** with strict schema output, vector retrieval, and SQL read-back |
| Semantic index | **8 documents / 8 chunks**, real 384-dimensional BGE embeddings and FAISS; unrelated-query and forecasting retrieval checks passed |
| npm dependency audit | **0 vulnerabilities** after Tailwind 4 update |
| Python dependency consistency | `pip check` passed |
| Secret-value scan | No configured secret values found in publishable source files; actual `.env` files, caches, databases, and dependencies are ignored |
| Branding cleanup | No old-company references found in application source, dataset, tests, package metadata, or deployment/documentation files |

## Live model and resolved issues

The previously configured `llama-3.3-70b-versatile` returned 404 and was absent from the account's available model list. The application now uses **`openai/gpt-oss-20b` through Groq**. The key was preserved.

JSON-only output occasionally failed local validation during browser testing. Groq strict schema mode, low reasoning effort, and a larger output budget resolved the tested failure. The final direct checks completed in approximately 2.3–2.8 seconds each; latency is not guaranteed. Provider timeouts and quota errors remain possible and are handled explicitly.

Port 8000 was occupied by an unrelated application. This project was tested on **backend port 8011** with the Vite proxy pointed there. The other application was not changed.

## Resource and deployment limits

The running local API measured about **156.7 MiB resident memory** after live browser tests; an earlier cold smoke process measured about 241 MiB. These are Windows measurements, not a substitute for Render container validation. Configuration uses one worker, one embedding thread, a quantized local model, a tiny index, and a free Render plan.

Docker engine was not running locally, so a local Docker image build has not been verified. Cloud deployment and URL checks are recorded here only after completion. SQLite is persistent locally but ephemeral on Render's free filesystem.

GitHub publishing and Vercel/Render free-plan deployment have been authorized by the owner for `cout1909/datatech-labs-ai-advisor`; authentication and remote verification are in progress.

The exact interviewing company has not been confirmed. The corpus intentionally contains labeled general engineering references, not unverified company-service claims.
