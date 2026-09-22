from pydantic import BaseModel, ConfigDict


class ConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subject: str | None
    description: str | None
    difficulty_level: int | None


class ConceptExtractionResult(BaseModel):
    subject: str
    filename: str
    created_count: int
    reused_count: int
    prerequisite_edge_count: int
    concepts: list[ConceptRead]
