import math
import re
from collections import Counter
from typing import Any

from fastapi import HTTPException

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

    references = load_material_references(material_id)

    if not references:
        raise HTTPException(
            status_code=404,
            detail="No hay referencias extraídas para este material.",
        )

    query_vector = build_vector(query)
    query_tokens = set(tokenize(query))

    scored = []

    for reference in references:
        text = str(reference.get("text") or reference.get("excerpt") or "")
        vector_score = cosine_similarity(query_vector, build_vector(text))
        keyword_score = keyword_overlap_score(query_tokens, text)
        final_score = (0.70 * vector_score) + (0.30 * keyword_score)

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


def build_context_from_references(references: list[dict[str, Any]]) -> str:
    lines = []

    for reference in references:
        page = reference.get("page")
        page_text = f"página {page}" if page else "sin página"
        lines.append(f"[{reference.get('ref_id')}] ({page_text}) {reference.get('text')}")

    return "\\n\\n".join(lines)


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
