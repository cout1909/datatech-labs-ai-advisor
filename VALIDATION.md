# Validation evidence

Run on 8 October 2026 using the existing project `.venv` (Python 3.12.10), Node 20.17.0, and installed Chrome.

| Check | Actual result |
| --- | --- |
| Backend pytest | **32 passed**, including input/schema checks, provider failure/retry behavior, real semantic retrieval, SQL writes/reads, persistence, isolation, and CORS |
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

Docker engine was not running locally, but Render successfully built and ran the Docker image. The public Vercel frontend and Render backend were verified, including actual cross-origin browser requests. SQLite is persistent locally but ephemeral on Render's free filesystem.

## Verified public deployment

- Repository: https://github.com/cout1909/datatech-labs-ai-advisor
- Frontend: https://datatech-labs-ai-advisor.vercel.app
- Backend: https://datatech-labs-ai-project-advisor-api.onrender.com
- Health and Swagger: `/health` and `/docs` on the backend returned success.
- GitHub CI: https://github.com/cout1909/datatech-labs-ai-advisor/actions/runs/37797402587 completed successfully for the deployed application revision.
- The public frontend completed three real analyses, displayed semantic source references, reopened SQL history, fit a 390px mobile viewport, and produced no browser console/page errors in the smoke run.
- Backend CORS permits the exact production frontend origin. The frontend build has the real Render URL.
- Vercel account plan: **Hobby**. Render compute plan: **free**, one instance, no paid disk.
- Render memory samples during verification reached **309,551,100 bytes (about 295 MiB)** against a reported **536,870,900-byte limit (512 MiB)**. This validates the observed demo workload, not arbitrary load.
- The workspace has another free Render service; monthly free instance hours are shared. Cold starts, quotas, and ephemeral SQLite remain limitations.
- A committed-tree check covered all 45 tracked files: no actual `.env` files, model caches, databases, or configured Groq key were committed. Only safe `.env.example` templates are tracked.

Groq occasionally rejected a generated structured response with a 400. The application now retries a provider-reported JSON validation failure once, within the existing two-attempt limit, and logs only a sanitized error code. The additional regression test passed. The final hosted browser and API checks succeeded.

The exact interviewing company has not been confirmed. The corpus intentionally contains labeled general engineering references, not unverified company-service claims.
