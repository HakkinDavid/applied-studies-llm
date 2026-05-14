import json
from pathlib import Path
from typing import Any

from app.core.paths import INDEX_FILE, KNOWLEDGE_FOREST_FILE, QUESTION_BANK_FILE, REFERENCES_DIR


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_index() -> dict[str, Any]:
    return load_json(INDEX_FILE, {})


def save_index(index: dict[str, Any]) -> None:
    save_json(INDEX_FILE, index)


def load_question_bank() -> list[dict[str, Any]]:
    data = load_json(QUESTION_BANK_FILE, [])
    return data if isinstance(data, list) else []


def save_question_bank(questions: list[dict[str, Any]]) -> None:
    save_json(QUESTION_BANK_FILE, questions)


def load_knowledge_forest() -> dict[str, Any]:
    forest = load_json(KNOWLEDGE_FOREST_FILE, {"trees": {}})

    if not isinstance(forest, dict):
        return {"trees": {}}

    if "trees" not in forest or not isinstance(forest["trees"], dict):
        forest["trees"] = {}

    return forest


def save_knowledge_forest(forest: dict[str, Any]) -> None:
    save_json(KNOWLEDGE_FOREST_FILE, forest)


def references_path(material_id: str) -> Path:
    return REFERENCES_DIR / f"{material_id}.json"


def load_material_references(material_id: str) -> list[dict[str, Any]]:
    data = load_json(references_path(material_id), [])
    return data if isinstance(data, list) else []


def save_material_references(material_id: str, references: list[dict[str, Any]]) -> None:
    save_json(references_path(material_id), references)
