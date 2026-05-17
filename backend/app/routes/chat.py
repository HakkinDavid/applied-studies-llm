from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat import ask_material_question, load_conversation


router = APIRouter()


class AskMaterialRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    top_k: int = 5


class AskMaterialResponse(BaseModel):
    conversation_id: str
    material_id: str
    material_name: str
    question: str
    answer: str
    confidence: Any = None
    suggested_follow_up: Any = None
    used_references: list[Any] = []
    retrieved_references: list[dict[str, Any]] = []


@router.post("/api/materials/{material_id}/ask", response_model=AskMaterialResponse)
def ask_material(material_id: str, payload: AskMaterialRequest):
    return ask_material_question(
        material_id=material_id,
        question=payload.question,
        conversation_id=payload.conversation_id,
        top_k=payload.top_k,
    )


@router.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    return load_conversation(conversation_id)
