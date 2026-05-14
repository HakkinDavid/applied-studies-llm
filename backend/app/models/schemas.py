from typing import Any, Optional

from pydantic import BaseModel


class MaterialResponse(BaseModel):
    id: str
    sha256: str
    original_filename: str
    stored_filename: str
    extension: str
    content_type: Optional[str]
    size_bytes: int
    text_chars: int
    reference_count: int = 0
    uploaded_at: str
    duplicate: bool
    generated_questions: int
    area: Optional[str] = None
    subarea: Optional[str] = None
    classification_summary: Optional[str] = None
    tree_id: Optional[str] = None
    tree_name: Optional[str] = None
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    leaf_id: Optional[str] = None
    leaf_name: Optional[str] = None
    knowledge_path: Optional[str] = None


class MaterialListResponse(BaseModel):
    total: int
    materials: list[dict[str, Any]]


class QuestionBankResponse(BaseModel):
    total: int
    questions: list[dict[str, Any]]


class KnowledgeForestResponse(BaseModel):
    total_trees: int
    forest: dict[str, Any]


class MaterialReferencesResponse(BaseModel):
    material_id: str
    total: int
    references: list[dict[str, Any]]
