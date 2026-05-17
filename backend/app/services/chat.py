import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.paths import STORAGE_DIR
from app.services.ai import call_ai_text
from app.services.rag import (
    build_context_from_conversation_messages,
    build_context_from_references,
    retrieve_relevant_conversation_messages,
    retrieve_relevant_references,
    summarize_conversation_retrieval,
    summarize_retrieval,
)
from app.services.storage import load_index, load_json, save_json
from app.services.utils import extract_json_from_model_text, now_iso


CONVERSATIONS_DIR = STORAGE_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(exist_ok=True)


def conversation_path(conversation_id: str) -> Path:
    return CONVERSATIONS_DIR / f"{conversation_id}.json"


def create_conversation_id() -> str:
    return str(uuid.uuid4())


def material_exists_or_404(material_id: str) -> dict[str, Any]:
    index = load_index()

    if material_id not in index:
        raise HTTPException(
            status_code=404,
            detail="Material no encontrado.",
        )

    return index[material_id]


def load_conversation(conversation_id: str) -> dict[str, Any]:
    path = conversation_path(conversation_id)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada.",
        )

    conversation = load_json(path, {})

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="La conversación existe, pero no se pudo leer correctamente.",
        )

    return conversation


def save_conversation(conversation: dict[str, Any]) -> None:
    conversation["updated_at"] = now_iso()
    save_json(conversation_path(conversation["conversation_id"]), conversation)


def create_material_conversation(
    material_id: str,
    title: str | None = None,
) -> dict[str, Any]:
    material = material_exists_or_404(material_id)
    conversation_id = create_conversation_id()
    material_name = material.get("original_filename", material_id)

    conversation = {
        "conversation_id": conversation_id,
        "material_id": material_id,
        "material_name": material_name,
        "title": title or f"Conversación sobre {material_name}",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "messages": [],
    }

    save_conversation(conversation)

    return {
        "conversation_id": conversation_id,
        "material_id": material_id,
        "material_name": material_name,
        "title": conversation["title"],
    }


def append_message(
    conversation: dict[str, Any],
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    conversation.setdefault("messages", []).append(
        {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now_iso(),
        }
    )


def build_material_question_prompt(
    material_name: str,
    user_question: str,
    material_context: str,
    conversation_context: str,
) -> str:
    return f"""
Responde la pregunta del usuario usando principalmente el material de estudio proporcionado.

Material:
{material_name}

Fragmentos relevantes del material:
{material_context}

Fragmentos relevantes de la conversación previa:
{conversation_context if conversation_context else "No hay conversación previa relevante."}

Pregunta actual del usuario:
{user_question}

Reglas:
- Responde en español.
- Usa el material como fuente principal.
- Usa los fragmentos de conversación solo para entender continuidad, referencias como "eso", "lo anterior" o preguntas de seguimiento.
- Si el material no contiene suficiente información, dilo claramente.
- No inventes datos fuera del material.
- Si puedes, menciona de forma natural la página o referencia usada.
- Responde preferentemente en JSON válido con el formato indicado.
- Si por alguna razón no puedes responder en JSON, responde texto normal.

Formato JSON preferido:
{{
  "answer": "Respuesta clara para el usuario",
  "used_references": ["id de referencia usada"],
  "confidence": "alta | media | baja",
  "suggested_follow_up": "Una pregunta sugerida para seguir estudiando"
}}
""".strip()


def parse_chat_model_response(content: str) -> dict[str, Any]:
    try:
        parsed = extract_json_from_model_text(content)

        if isinstance(parsed, dict):
            answer = str(parsed.get("answer") or "").strip()

            if answer:
                return {
                    "answer": answer,
                    "used_references": parsed.get("used_references", []),
                    "confidence": parsed.get("confidence", "media"),
                    "suggested_follow_up": parsed.get("suggested_follow_up"),
                    "raw_response": parsed,
                }
    except Exception:
        pass

    clean = content.strip()

    if not clean:
        raise HTTPException(
            status_code=500,
            detail="El modelo respondió vacío.",
        )

    return {
        "answer": clean,
        "used_references": [],
        "confidence": "media",
        "suggested_follow_up": None,
        "raw_response": clean,
    }


def answer_question_in_conversation(
    conversation: dict[str, Any],
    question: str,
    top_k: int = 5,
    conversation_top_k: int = 6,
) -> dict[str, Any]:
    material_id = conversation.get("material_id")

    if not material_id:
        raise HTTPException(
            status_code=400,
            detail="La conversación no tiene material asociado.",
        )

    material = material_exists_or_404(material_id)
    material_name = material.get("original_filename", material_id)

    if not question.strip():
        raise HTTPException(
            status_code=400,
            detail="La pregunta no puede estar vacía.",
        )

    if top_k < 1 or top_k > 12:
        raise HTTPException(
            status_code=400,
            detail="top_k debe estar entre 1 y 12.",
        )

    if conversation_top_k < 0 or conversation_top_k > 20:
        raise HTTPException(
            status_code=400,
            detail="conversation_top_k debe estar entre 0 y 20.",
        )

    material_references = retrieve_relevant_references(
        material_id=material_id,
        query=question,
        top_k=top_k,
    )

    conversation_messages = retrieve_relevant_conversation_messages(
        conversation=conversation,
        query=question,
        top_k=conversation_top_k,
    )

    material_context = build_context_from_references(material_references)
    conversation_context = build_context_from_conversation_messages(conversation_messages)

    prompt = build_material_question_prompt(
        material_name=material_name,
        user_question=question,
        material_context=material_context,
        conversation_context=conversation_context,
    )

    content = call_ai_text(
        system_message="Eres un tutor académico que responde preguntas usando material de estudio y contexto conversacional recuperado por RAG.",
        user_message=prompt,
        temperature=0.3,
    )

    parsed = parse_chat_model_response(content)
    answer = parsed["answer"]

    retrieved_references = summarize_retrieval(material_references)
    retrieved_conversation_messages = summarize_conversation_retrieval(conversation_messages)

    append_message(
        conversation,
        role="user",
        content=question,
        metadata={
            "material_id": material_id,
            "top_k": top_k,
            "conversation_top_k": conversation_top_k,
        },
    )

    append_message(
        conversation,
        role="assistant",
        content=answer,
        metadata={
            "material_id": material_id,
            "confidence": parsed.get("confidence", "media"),
            "suggested_follow_up": parsed.get("suggested_follow_up"),
            "used_references": parsed.get("used_references", []),
            "retrieved_references": retrieved_references,
            "retrieved_conversation_messages": retrieved_conversation_messages,
        },
    )

    save_conversation(conversation)

    return {
        "conversation_id": conversation["conversation_id"],
        "material_id": material_id,
        "material_name": material_name,
        "question": question,
        "answer": answer,
        "confidence": parsed.get("confidence", "media"),
        "suggested_follow_up": parsed.get("suggested_follow_up"),
        "used_references": parsed.get("used_references", []),
        "retrieved_references": retrieved_references,
        "retrieved_conversation_messages": retrieved_conversation_messages,
    }


def ask_material_once(
    material_id: str,
    question: str,
    top_k: int = 5,
    conversation_top_k: int = 6,
) -> dict[str, Any]:
    created = create_material_conversation(material_id)
    conversation = load_conversation(created["conversation_id"])

    return answer_question_in_conversation(
        conversation=conversation,
        question=question,
        top_k=top_k,
        conversation_top_k=conversation_top_k,
    )


def post_message_to_conversation(
    conversation_id: str,
    question: str,
    top_k: int = 5,
    conversation_top_k: int = 6,
) -> dict[str, Any]:
    conversation = load_conversation(conversation_id)

    return answer_question_in_conversation(
        conversation=conversation,
        question=question,
        top_k=top_k,
        conversation_top_k=conversation_top_k,
    )


def list_conversations() -> dict[str, Any]:
    conversations = []

    for path in CONVERSATIONS_DIR.glob("*.json"):
        conversation = load_json(path, {})

        if not conversation:
            continue

        conversations.append(
            {
                "conversation_id": conversation.get("conversation_id"),
                "material_id": conversation.get("material_id"),
                "material_name": conversation.get("material_name"),
                "title": conversation.get("title"),
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
                "message_count": len(conversation.get("messages", [])),
            }
        )

    conversations.sort(key=lambda item: item.get("updated_at") or "", reverse=True)

    return {
        "total": len(conversations),
        "conversations": conversations,
    }


def list_material_conversations(material_id: str) -> dict[str, Any]:
    material_exists_or_404(material_id)
    all_conversations = list_conversations()["conversations"]

    material_conversations = [
        conversation
        for conversation in all_conversations
        if conversation.get("material_id") == material_id
    ]

    return {
        "material_id": material_id,
        "total": len(material_conversations),
        "conversations": material_conversations,
    }