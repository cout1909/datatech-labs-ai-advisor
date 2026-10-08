# Knowledge base and source decisions

Reviewed: 8 October 2026.

## Company identity

The interview company was identified as DataTech Labs, but its official website or job-posting URL has not yet been provided. Public search surfaced The DataTech Labs Inc (TDTL), associated with https://tdtl.world/, as a possible match. The homepage is JavaScript-rendered in the available reader. There is no confirmed link between this entity and the specific interview invitation.

**Decision:** Do not add company-specific claims until the match is confirmed. The product name reflects the interview context. All current records are `general_reference`, and the knowledge status endpoint reports that company identity is not verified.

## Indexed sources

These are concise paraphrases of official technical documentation. Search tags are editorial hints, not company-service claims.

| ID | Reference and scope |
| --- | --- |
| enterprise-search | [LangChain retrieval](https://docs.langchain.com/oss/python/deepagents/retrieval): external context, embeddings, vector stores, two-step RAG |
| customer-support | [LangChain retrieval](https://docs.langchain.com/oss/python/deepagents/retrieval): FAQ/documentation bots; editorial application to support questions |
| document-processing | [Microsoft Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview?view=doc-intel-4.0.0): text, tables, fields, extraction models |
| supervised-learning | [scikit-learn supervised learning](https://scikit-learn.org/stable/supervised_learning.html): classification/regression model families |
| predictive-analytics | [Time-series example](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html): lagged features and time-aware evaluation |
| workflow-automation | [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents): fixed workflows versus dynamic decisions |
| human-review | [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop): approve, edit, reject actions |
| deployment | [Render Blueprint](https://render.com/docs/blueprint-spec): runtime, environment, health checks |

## Metadata and maintenance

Every JSON record contains an ID, title, description, URL, document type, use-case tags, and verification date. Indexing assigns `document-id:chunk-number` identifiers; retrieval passes the actual matched chunk text and metadata. Keyword fallback uses `document-id:document` rather than pretending a vector chunk was retrieved.

The index manifest records a dataset SHA-256 hash and embedding model ID. After editing `backend/app/data/knowledge.json`, run `python -m app.services.rag_service` from `backend`. The Docker build performs the same step. Review sources periodically.

A company reference requires a confirmed organization match, reviewed official URL, accurate summary, `company_reference` metadata, and matching documentation/test updates. Never relabel general technical advice as an official offering.
