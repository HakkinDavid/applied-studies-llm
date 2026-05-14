import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "sin-nombre"


def extract_json_from_model_text(text: str) -> Any:
    clean = text.strip()

    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"```$", "", clean).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", clean, flags=re.DOTALL)

    if not match:
        raise HTTPException(
            status_code=500,
            detail="El modelo no devolvió JSON válido.",
        )

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="No se pudo interpretar el JSON generado por el modelo.",
        )
