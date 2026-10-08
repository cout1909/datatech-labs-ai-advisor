from typing import Annotated, Literal
from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_problem: Annotated[str, StringConstraints(strip_whitespace=True, min_length=20, max_length=4000)] = Field(validation_alias=AliasChoices("problem", "business_problem"))
    industry: Literal["Finance", "Healthcare", "Retail", "Manufacturing", "IT Services", "Other"] | None = None

class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    solution_name: Text
    problem_summary: Text
    recommended_approach: Text
    reasoning: Text
    human_oversight: Text
    architecture_steps: list[Text] = Field(min_length=3, max_length=8)
    suggested_technologies: list[Text] = Field(min_length=1, max_length=10)
    implementation_roadmap: list[Text] = Field(min_length=3, max_length=8)
    expected_benefits: list[Text] = Field(min_length=1, max_length=6)
    considerations: list[Text] = Field(min_length=1, max_length=6)

class SourceReference(BaseModel):
    id: str
    title: str
    url: str
    description: str
    verified_on: str
    document_type: Literal["general_reference", "company_reference"]
    chunk_id: str

class AnalyzeResponse(Recommendation):
    source_references: list[SourceReference]
    retrieval_mode: Literal["vector", "keyword_fallback"]
    grounding_note: str
    generation_mode: Literal["live"] = "live"

class SavedAnalysis(AnalyzeResponse):
    analysis_id: str
    created_at: datetime

class HistoryItem(BaseModel):
    id: str
    problem: str
    industry: str | None
    solution_name: str
    created_at: datetime
    status: Literal["completed"]

class HistoryPage(BaseModel):
    items: list[HistoryItem]
    total: int
    limit: int
    offset: int

class HistoryDetail(HistoryItem):
    recommendation: AnalyzeResponse
