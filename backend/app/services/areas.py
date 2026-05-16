from typing import Any

from app.services.storage import load_knowledge_forest, load_question_bank


def clean_area_name(area: Any) -> str | None:
    if not isinstance(area, str):
        return None

    clean = area.strip()

    if not clean:
        return None

    return clean


def get_areas_from_question_bank() -> list[str]:
    questions = load_question_bank()
    areas = set()

    for question in questions:
        area = clean_area_name(question.get("area"))

        if area:
            areas.add(area)

    return sorted(areas)


def get_areas_from_forest() -> list[str]:
    forest = load_knowledge_forest()
    areas = set()

    for tree in forest.get("trees", {}).values():
        for node in tree.get("nodes", {}).values():
            node_name = clean_area_name(node.get("name"))

            if node_name:
                areas.add(node_name)

    return sorted(areas)


def get_dynamic_areas() -> list[str]:
    areas = set()

    for area in get_areas_from_question_bank():
        areas.add(area)

    for area in get_areas_from_forest():
        areas.add(area)

    return sorted(areas)


def format_areas_for_prompt() -> str:
    areas = get_dynamic_areas()

    if not areas:
        return "No existen áreas previas. Debes proponer una nueva área clara y académica."

    return "\n".join(f"- {area}" for area in areas)


def normalize_dynamic_area(area: Any, fallback: str = "Área general") -> str:
    clean = clean_area_name(area)

    if clean:
        return clean

    return fallback