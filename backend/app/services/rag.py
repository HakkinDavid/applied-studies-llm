import math
import re
from collections import Counter
from typing import Any

from fastapi import HTTPException

from app.core.paths import TEXTS_DIR
from app.services.storage import load_index, load_material_references


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-záéíóúñü0-9]+", text.lower())


def build_vector(text: str) -> Counter:
    return Counter(tokenize(text))


def cosine_similarity(left: Counter, right: Counter) -> float:
    common = set(left) & set(right)

    numerator = sum(left[token] * right[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


def keyword_overlap_score(query_tokens: set[str], text: str) -> float:
    if not query_tokens:
        return 0.0

    text_tokens = set(tokenize(text))
    matches = query_tokens & text_tokens

    return len(matches) / len(query_tokens)


def make_excerpt(text: str, max_chars: int = 420) -> str:
    clean = re.sub(r"\s+", " ", text).strip()

    if len(clean) <= max_chars:
        return clean

    return clean[:max_chars].rstrip() + "..."


def split_text_into_references(text: str, max_chars: int = 1200) -> list[dict[str, Any]]:
    clean = re.sub(r"\s+", " ", text).strip()

    if not clean:
        return []

    references = []
    start = 0
    counter = 1

    while start < len(clean):
        end = min(start + max_chars, len(clean))
        piece = clean[start:end].strip()

        if piece:
            references.append(
                {
                    "ref_id": f"txt-{counter}",
                    "page": None,
                    "excerpt": make_excerpt(piece),
                    "text": piece,
                }
            )

        start = end
        counter += 1

    return references


def load_references_or_fallback(material_id: str) -> list[dict[str, Any]]:
    references = load_material_references(material_id)

    if references:
        return references

    text_path = TEXTS_DIR / f"{material_id}.txt"

    if not text_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No hay referencias ni texto extraído para este material. Vuelve a subir el documento para regenerar sus datos.",
        )

    text = text_path.read_text(encoding="utf-8")
    references = split_text_into_references(text)

    if not references:
        raise HTTPException(
            status_code=404,
            detail="El material no tiene texto útil para responder preguntas.",
        )

    return references


def score_text(query: str, text: str) -> float:
    query_vector = build_vector(query)
    text_vector = build_vector(text)
    query_tokens = set(tokenize(query))

    vector_score = cosine_similarity(query_vector, text_vector)
    keyword_score = keyword_overlap_score(query_tokens, text)

    return (0.70 * vector_score) + (0.30 * keyword_score)


def retrieve_relevant_references(
    material_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    index = load_index()

    if material_id not in index:
        raise HTTPException(
            status_code=404,
            detail="Material no encontrado.",
        )

    references = load_references_or_fallback(material_id)
    scored = []

    for reference in references:
        text = str(reference.get("text") or reference.get("excerpt") or "")
        final_score = score_text(query, text)

        scored.append(
            {
                "ref_id": reference.get("ref_id"),
                "page": reference.get("page"),
                "excerpt": reference.get("excerpt"),
                "text": text,
                "score": round(final_score, 6),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)

    selected = [item for item in scored[:top_k] if item["score"] > 0]

    if not selected:
        selected = scored[:top_k]

    return selected


def retrieve_relevant_conversation_messages(
    conversation: dict[str, Any],
    query: str,
    top_k: int = 6,
) -> list[dict[str, Any]]:
    messages = conversation.get("messages", [])

    scored = []

    for index, message in enumerate(messages):
        role = message.get("role")
        content = str(message.get("content") or "").strip()

        if role not in ["user", "assistant"]:
            continue

        if not content:
            continue

        final_score = score_text(query, content)

        scored.append(
            {
                "message_index": index,
                "role": role,
                "content": content,
                "created_at": message.get("created_at"),
                "score": round(final_score, 6),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)

    selected = [item for item in scored[:top_k] if item["score"] > 0]

    if not selected:
        selected = scored[-top_k:]

    selected.sort(key=lambda item: item["message_index"])

    return selected


def build_context_from_references(references: list[dict[str, Any]]) -> str:
    lines = []

    for reference in references:
        page = reference.get("page")
        page_text = f"página {page}" if page else "sin página"

        lines.append(
            f"[{reference.get('ref_id')}] ({page_text}) {reference.get('text')}"
        )

    return "\n\n".join(lines)


def build_context_from_conversation_messages(messages: list[dict[str, Any]]) -> str:
    lines = []

    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        index = message.get("message_index")

        lines.append(f"[mensaje {index} - {role}] {content}")

    return "\n\n".join(lines)


def summarize_retrieval(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ref_id": reference.get("ref_id"),
            "page": reference.get("page"),
            "excerpt": reference.get("excerpt"),
            "score": reference.get("score"),
        }
        for reference in references
    ]


def summarize_conversation_retrieval(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "message_index": message.get("message_index"),
            "role": message.get("role"),
            "content": make_excerpt(message.get("content", "")),
            "created_at": message.get("created_at"),
            "score": message.get("score"),
        }
        for message in messages
    ]