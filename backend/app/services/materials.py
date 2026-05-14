from typing import Any, Optional

from app.services.forest import classify_material_for_forest, update_knowledge_forest
from app.services.questions import add_questions_to_bank, generate_questions_with_ai
from app.services.storage import load_knowledge_forest
from app.services.utils import now_iso


def build_material_metadata(
    sha256: str,
    original_filename: str,
    stored_filename: str,
    extension: str,
    content_type: Optional[str],
    size_bytes: int,
    text_chars: int,
    reference_count: int,
    duplicate: bool,
    generated_questions: int,
    frontend_area: str,
    classification_summary: str,
    forest_location: dict[str, str],
) -> dict[str, Any]:
    return {
        "id": sha256,
        "sha256": sha256,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "extension": extension,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "text_chars": text_chars,
        "reference_count": reference_count,
        "uploaded_at": now_iso(),
        "duplicate": duplicate,
        "generated_questions": generated_questions,
        "area": frontend_area,
        "subarea": forest_location["leaf_name"],
        "classification_summary": classification_summary,
        "tree_id": forest_location["tree_id"],
        "tree_name": forest_location["tree_name"],
        "node_id": forest_location["node_id"],
        "node_name": forest_location["node_name"],
        "leaf_id": forest_location["leaf_id"],
        "leaf_name": forest_location["leaf_name"],
        "knowledge_path": forest_location["knowledge_path"],
    }


def process_material_text(
    cleaned_text: str,
    references: list[dict[str, Any]],
    sha256: str,
    original_filename: str,
    num_questions: int,
    tree_hint: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int, str, str, dict[str, str]]:
    forest = load_knowledge_forest()

    classification = classify_material_for_forest(
        text=cleaned_text,
        forest=forest,
        tree_hint=tree_hint,
    )

    frontend_area = classification["frontend_area"]

    forest_location = update_knowledge_forest(
        classification=classification,
        material_id=sha256,
        generated_questions=0,
    )

    generated_questions = generate_questions_with_ai(
        text=cleaned_text,
        references=references,
        material_id=sha256,
        original_filename=original_filename,
        num_questions=num_questions,
        frontend_area=frontend_area,
        forest_location=forest_location,
    )

    added_questions = add_questions_to_bank(generated_questions)

    if added_questions > 0:
        update_knowledge_forest(
            classification=classification,
            material_id=sha256,
            generated_questions=added_questions,
        )

    return (
        generated_questions,
        added_questions,
        frontend_area,
        classification["summary"],
        forest_location,
    )
