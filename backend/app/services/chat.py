import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.paths import STORAGE_DIR
from app.services.ai import call_ai_json
from app.services.rag import build_context_from_references, retrieve_relevant_references, summarize_retrieval
from app.services.storage import load_index, load_json, save_json
from app.services.utils import now_iso


CONVERSATIONS_DIR = STORAGE_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(exist_ok=True)


def conversation_path(conversation_id: str) -> Path:
    return CONVERSATIONS_DIR / f"{conversation_id}.json"


def create_conversation_id() -> str:
    return str(uuid.uuid4())


def load_conversation(conversation_id: str) -> dict[str, Any]:
    return load_json(
        conversation_path(conversation_id),
        {
            "conversation_id": conversation_id,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "messages": [],
        },
    )


def save_conversation(conversation: dict[str, Any]) -> None:
    conversation["updated_at"] = now_iso()
    save_json(conversation_path(conversation["conversation_id"]), conversation)


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


def get_recent_conversation_text(conversation: dict[str, Any], limit: int = 8) -> str:
    messages = conversation.get("messages", [])[-limit:]
    lines = []

    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        lines.append(f"{role}: {content}")

    return "\\n".join(lines)


def ask_material_question(
    material_id: str,
    question: str,
    conversation_id: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    index = load_index()

    if material_id not in index:
        raise HTTPException(
            status_code=404,
            detail="Material no encontrado.",
        )

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

    material = index[material_id]
    material_name = material.get("original_filename", material_id)

    if not conversation_id:
        conversation_id = create_conversation_id()

    conversation = load_conversation(conversation_id)
    references = retrieve_relevant_references(material_id, question, top_k=top_k)
    context = build_context_from_references(references)
    history = get_recent_conversation_text(conversation)

    prompt = f"""
Responde la pregunta del usuario usando principalmente el material de estudio proporcionado.

Material:
{material_name}

Historial reciente:
{history if history else "No hay historial previo."}

Fragmentos relevantes del material:
{context}

Pregunta del usuario:
{question}

Reglas:
- Responde en español.
- Usa el material como fuente principal.
- Si el material no contiene suficiente información, dilo claramente.
- No inventes datos fuera del material.
- Si puedes, menciona la página o referencia usada.
- Responde únicamente JSON válido.

Formato:
{{
  "answer": "Respuesta clara para el usuario",
  "used_references": ["id de referencia usada"],
  "confidence": "alta | media | baja",
  "suggested_follow_up": "Una pregunta sugerida para seguir estudiando"
}}
""".strip()

    parsed = call_ai_json(
        system_message="Eres un tutor académico que responde preguntas usando material de estudio y referencias documentales. Respondes únicamente JSON válido.",
        user_message=prompt,
        temperature=0.3,
    )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail="La respuesta del modelo no tiene formato válido.",
        )

    answer = str(parsed.get("answer") or "").strip()

    if not answer:
        raise HTTPException(
            status_code=500,
            detail="La respuesta del modelo no incluyó una respuesta válida.",
        )

    append_message(conversation, "user", question, {"material_id": material_id})
    append_message(
        conversation,
        "assistant",
        answer,
        {
            "material_id": material_id,
            "retrieved_references": summarize_retrieval(references),
        },
    )
    save_conversation(conversation)

    return {
        "conversation_id": conversation_id,
        "material_id": material_id,
        "material_name": material_name,
        "question": question,
        "answer": answer,
        "confidence": parsed.get("confidence", "media"),
        "suggested_follow_up": parsed.get("suggested_follow_up"),
        "used_references": parsed.get("used_references", []),
        "retrieved_references": summarize_retrieval(references),
    }
