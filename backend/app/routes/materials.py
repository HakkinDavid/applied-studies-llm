from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import DEFAULT_QUESTION_COUNT
from app.core.paths import TEXTS_DIR, UPLOADS_DIR
from app.models.schemas import MaterialListResponse, MaterialReferencesResponse, MaterialResponse
from app.services.deletion import delete_material_by_id
from app.services.files import calculate_sha256, validate_file
from app.services.materials import build_material_metadata, process_material_text
from app.services.storage import (
    load_index,
    load_material_references,
    load_question_bank,
    save_index,
    save_material_references,
)
from app.services.text import clean_references, clean_text, extract_text_and_references


router = APIRouter()


@router.post("/api/materials/upload", response_model=MaterialResponse)
async def upload_material(
    file: UploadFile = File(...),
    tree_hint: Optional[str] = Form(default=None),
    num_questions: int = Form(default=DEFAULT_QUESTION_COUNT),
):
    original_filename = file.filename or "archivo_sin_nombre"
    data = await file.read()

    extension = validate_file(original_filename, data)
    sha256 = calculate_sha256(data)

    stored_filename = f"{sha256}{extension}"
    stored_path = UPLOADS_DIR / stored_filename
    text_path = TEXTS_DIR / f"{sha256}.txt"

    index = load_index()
    duplicate = sha256 in index

    if num_questions < 1 or num_questions > 40:
        raise HTTPException(
            status_code=400,
            detail="El número de preguntas debe estar entre 1 y 40.",
        )

    if duplicate:
        metadata = dict(index[sha256])

        existing_questions = [
            question for question in load_question_bank()
            if question.get("source_material_id") == sha256
        ]

        if existing_questions:
            metadata["duplicate"] = True
            metadata["generated_questions"] = len(existing_questions)
            return MaterialResponse(**metadata)

        if not text_path.exists():
            raise HTTPException(
                status_code=409,
                detail="El archivo ya estaba registrado, pero no se encontró el texto extraído. Borra el material y vuelve a subirlo.",
            )

        with text_path.open("r", encoding="utf-8") as text_file:
            cleaned_text = text_file.read()

        references = load_material_references(sha256)

        if not references:
            references = [
                {
                    "ref_id": "doc-1",
                    "page": None,
                    "excerpt": cleaned_text[:420],
                    "text": cleaned_text,
                }
            ]
            save_material_references(sha256, references)

        _, added_questions, frontend_area, classification_summary, forest_location = process_material_text(
            cleaned_text=cleaned_text,
            references=references,
            sha256=sha256,
            original_filename=metadata.get("original_filename", original_filename),
            num_questions=num_questions,
            tree_hint=tree_hint,
        )

        metadata["duplicate"] = True
        metadata["generated_questions"] = added_questions
        metadata["reference_count"] = len(references)
        metadata["area"] = frontend_area
        metadata["subarea"] = forest_location["leaf_name"]
        metadata["classification_summary"] = classification_summary
        metadata["tree_id"] = forest_location["tree_id"]
        metadata["tree_name"] = forest_location["tree_name"]
        metadata["node_id"] = forest_location["node_id"]
        metadata["node_name"] = forest_location["node_name"]
        metadata["leaf_id"] = forest_location["leaf_id"]
        metadata["leaf_name"] = forest_location["leaf_name"]
        metadata["knowledge_path"] = forest_location["knowledge_path"]

        index[sha256] = metadata
        save_index(index)

        return MaterialResponse(**metadata)

    extracted_text, references = extract_text_and_references(data, extension)
    cleaned_text = clean_text(extracted_text)
    cleaned_references = clean_references(references)

    if len(cleaned_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="El archivo tiene muy poco texto útil para generar preguntas.",
        )

    if not cleaned_references:
        cleaned_references = [
            {
                "ref_id": "doc-1",
                "page": None,
                "excerpt": cleaned_text[:420],
                "text": cleaned_text,
            }
        ]

    _, added_questions, frontend_area, classification_summary, forest_location = process_material_text(
        cleaned_text=cleaned_text,
        references=cleaned_references,
        sha256=sha256,
        original_filename=original_filename,
        num_questions=num_questions,
        tree_hint=tree_hint,
    )

    stored_path.write_bytes(data)

    with text_path.open("w", encoding="utf-8") as text_file:
        text_file.write(cleaned_text)

    save_material_references(sha256, cleaned_references)

    metadata = build_material_metadata(
        sha256=sha256,
        original_filename=original_filename,
        stored_filename=stored_filename,
        extension=extension,
        content_type=file.content_type,
        size_bytes=len(data),
        text_chars=len(cleaned_text),
        reference_count=len(cleaned_references),
        duplicate=False,
        generated_questions=added_questions,
        frontend_area=frontend_area,
        classification_summary=classification_summary,
        forest_location=forest_location,
    )

    index[sha256] = metadata
    save_index(index)

    return MaterialResponse(**metadata)


@router.get("/api/materials", response_model=MaterialListResponse)
def list_materials():
    index = load_index()
    materials = list(index.values())
    materials.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)

    return MaterialListResponse(
        total=len(materials),
        materials=materials,
    )


@router.get("/api/materials/{material_id}/references", response_model=MaterialReferencesResponse)
def get_material_references(material_id: str):
    references = load_material_references(material_id)

    return MaterialReferencesResponse(
        material_id=material_id,
        total=len(references),
        references=references,
    )



@router.delete("/api/materials/{material_id}")
def delete_material(material_id: str):
    return delete_material_by_id(material_id)
