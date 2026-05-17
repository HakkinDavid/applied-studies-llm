from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat import (
    ask_material_question,
    create_material_conversation,
    list_conversations,
    list_material_conversations,
    load_conversation,
    post_message_to_conversation,
)


router = APIRouter()


class CreateConversationRequest(BaseModel):
    title: str | None = None


class CreateConversationResponse(BaseModel):
    conversation_id: str
    material_id: str
    material_name: str
    title: str


class AskMaterialRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    top_k: int = 5


class ConversationMessageRequest(BaseModel):
    question: str
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


@router.post(
    "/api/materials/{material_id}/conversations",
    response_model=CreateConversationResponse,
)
def create_conversation_for_material(
    material_id: str,
    payload: CreateConversationRequest | None = None,
):
    title = payload.title if payload else None

    return create_material_conversation(
        material_id=material_id,
        title=title,
    )


@router.get("/api/materials/{material_id}/conversations")
def get_material_conversations(material_id: str):
    return list_material_conversations(material_id)


@router.post("/api/materials/{material_id}/ask", response_model=AskMaterialResponse)
def ask_material(material_id: str, payload: AskMaterialRequest):
    return ask_material_question(
        material_id=material_id,
        question=payload.question,
        conversation_id=payload.conversation_id,
        top_k=payload.top_k,
    )


@router.post(
    "/api/conversations/{conversation_id}/messages",
    response_model=AskMaterialResponse,
)
def post_conversation_message(
    conversation_id: str,
    payload: ConversationMessageRequest,
):
    return post_message_to_conversation(
        conversation_id=conversation_id,
        question=payload.question,
        top_k=payload.top_k,
    )


@router.get("/api/conversations")
def get_conversations():
    return list_conversations()


@router.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    return load_conversation(conversation_id)
