from starlette.concurrency import run_in_threadpool
from app.schemas import AnalyzeResponse, SourceReference
from app.services.llm_service import generate

async def analyze(request, retriever):
    documents, mode = await run_in_threadpool(retriever.search, request.business_problem)
    recommendation = await generate(request.business_problem, request.industry, documents)
    # Citation fields are populated from trusted local records, never model output.
    return AnalyzeResponse(**recommendation.model_dump(),
        source_references=[SourceReference(**{k: d[k] for k in SourceReference.model_fields}) for d in documents],
        retrieval_mode=mode,
        grounding_note=("Retrieved references are labeled by type. General engineering references are not DataTech Labs offerings. This architecture and roadmap are independent proposals requiring review."
                        if documents else "No useful knowledge reference was found. This is a general technical proposal, not a verified DataTech Labs offering."))
