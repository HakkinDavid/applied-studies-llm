import hashlib
from typing import Any, Optional

from fastapi import HTTPException

from app.core.config import MAX_REFERENCES_FOR_PROMPT
from app.services.areas import format_areas_for_prompt, normalize_dynamic_area
from app.services.ai import call_ai_json
from app.services.storage import load_question_bank, save_question_bank
from app.services.text import limit_text_for_generation, references_for_prompt


def build_question_id(material_id: str, question_text: str) -> str:
    raw = f"{material_id}:{question_text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def normalize_answer(answer: Any) -> int:
    if isinstance(answer, int) and 0 <= answer <= 3:
        return answer

    if isinstance(answer, str):
        value = answer.strip().upper()

        if value in ["0", "1", "2", "3"]:
            return int(value)

        if value in ["A", "B", "C", "D"]:
            return ["A", "B", "C", "D"].index(value)

    return 0


def get_reference_by_id(references: list[dict[str, Any]], ref_id: Any) -> Optional[dict[str, Any]]:
    if not ref_id:
        return None

    clean_ref_id = str(ref_id).strip()

    for reference in references:
        if str(reference.get("ref_id")) == clean_ref_id:
            return reference

    return None


def fallback_reference(references: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    return references[0] if references else None


def normalize_question(
    raw_question: dict[str, Any],
    material_id: str,
    original_filename: str,
    frontend_area: str,
    subarea: str,
    forest_location: dict[str, str],
    references: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    q = str(raw_question.get("q") or raw_question.get("question") or "").strip()
    options = raw_question.get("options")

    if not q or not isinstance(options, list) or len(options) != 4:
        return None

    clean_options = [str(option).strip() for option in options]

    if any(not option for option in clean_options):
        return None

    reference = get_reference_by_id(references, raw_question.get("source_ref_id"))

    if reference is None:
        reference = fallback_reference(references)

    source_ref_id = reference.get("ref_id") if reference else None
    source_page = reference.get("page") if reference else None
    source_excerpt = reference.get("excerpt") if reference else None

    return {
        "question_id": build_question_id(material_id, q),
        "q": q,
        "options": clean_options,
        "answer": normalize_answer(raw_question.get("answer")),
        "area": normalize_dynamic_area(raw_question.get("area") or frontend_area),
        "subarea": str(raw_question.get("subarea") or subarea).strip(),
        "synthetic": True,
        "source_material_id": material_id,
        "source_document_id": material_id,
        "source_document_name": original_filename,
        "source_ref_id": source_ref_id,
        "source_page": source_page,
        "source_excerpt": source_excerpt,
        "tree_id": forest_location["tree_id"],
        "tree_name": forest_location["tree_name"],
        "node_id": forest_location["node_id"],
        "node_name": forest_location["node_name"],
        "leaf_id": forest_location["leaf_id"],
        "leaf_name": forest_location["leaf_name"],
        "knowledge_path": forest_location["knowledge_path"],
    }


def build_question_generation_prompt(
    text: str,
    references: list[dict[str, Any]],
    num_questions: int,
    frontend_area: str,
    forest_location: dict[str, str],
) -> str:
    suggested_areas = format_areas_for_prompt()
    reference_block = references_for_prompt(references, max_items=MAX_REFERENCES_FOR_PROMPT)

    return f"""
Genera un banco de preguntas para un simulador de examen.

Debes basarte únicamente en el material proporcionado.
No inventes conceptos que no estén relacionados con el documento.
Genera exactamente {num_questions} preguntas.
Todas deben ser de opción múltiple.
Cada pregunta debe tener exactamente 4 opciones.
La respuesta correcta debe indicarse como número entero:
0 primera opción, 1 segunda opción, 2 tercera opción, 3 cuarta opción.

Ubicación del material en el bosque de conocimiento:
Árbol: {forest_location["tree_name"]}
Nodo: {forest_location["node_name"]}
Hoja: {forest_location["leaf_name"]}
Ruta: {forest_location["knowledge_path"]}

Referencias disponibles del documento:
{reference_block}

Áreas existentes detectadas:
{suggested_areas}

Formato exacto esperado:
[
  {{
    "q": "Texto de la pregunta",
    "options": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
    "answer": 0,
    "area": "{frontend_area}",
    "subarea": "Tema específico",
    "synthetic": true,
    "source_ref_id": "p1-1"
  }}
]

Reglas:
- Responde solamente con JSON válido.
- No uses markdown.
- No agregues explicaciones fuera del JSON.
- El campo "q" debe contener la pregunta.
- El campo "options" debe contener 4 respuestas posibles.
- El campo "answer" debe ser un número de 0 a 3.
- El campo "synthetic" siempre debe ser true.
- El campo "source_ref_id" debe ser uno de los ids de referencias disponibles.
- Si la pregunta corresponde claramente a una de las áreas existentes, usa exactamente ese mismo nombre en "area".
- Si no corresponde a ninguna, usa esta nueva área propuesta para este material: {frontend_area}.
- No inventes áreas diferentes entre preguntas del mismo documento si todas pertenecen al mismo tema.
- No crees variantes innecesarias de áreas ya existentes.
- El campo "subarea" debe relacionarse con la hoja del bosque: {forest_location["leaf_name"]}.
- Las preguntas deben evaluar comprensión, no solo memorización literal.
- Evita preguntas ambiguas.
- Evita opciones obviamente incorrectas.
- No menciones "según el documento" en cada pregunta.

Material completo:
{limit_text_for_generation(text)}
""".strip()


def generate_questions_with_ai(
    text: str,
    references: list[dict[str, Any]],
    material_id: str,
    original_filename: str,
    num_questions: int,
    frontend_area: str,
    forest_location: dict[str, str],
) -> list[dict[str, Any]]:
    prompt = build_question_generation_prompt(
        text=text,
        references=references,
        num_questions=num_questions,
        frontend_area=frontend_area,
        forest_location=forest_location,
    )

    parsed = call_ai_json(
        system_message="Eres un profesor que genera preguntas de examen con referencias documentales. Respondes únicamente con JSON válido.",
        user_message=prompt,
        temperature=0.4,
    )

    if isinstance(parsed, dict):
        raw_questions = parsed.get("questions", [])
    elif isinstance(parsed, list):
        raw_questions = parsed
    else:
        raw_questions = []

    normalized = []

    for raw_question in raw_questions:
        if isinstance(raw_question, dict):
            question = normalize_question(
                raw_question=raw_question,
                material_id=material_id,
                original_filename=original_filename,
                frontend_area=frontend_area,
                subarea=forest_location["leaf_name"],
                forest_location=forest_location,
                references=references,
            )

            if question:
                normalized.append(question)

    if not normalized:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron generar preguntas válidas.",
        )

    return normalized


def add_questions_to_bank(new_questions: list[dict[str, Any]]) -> int:
    bank = load_question_bank()

    existing_keys = {
        question.get("q", "").strip().lower()
        for question in bank
    }

    added = 0

    for question in new_questions:
        key = question.get("q", "").strip().lower()

        if key and key not in existing_keys:
            bank.append(question)
            existing_keys.add(key)
            added += 1

    save_question_bank(bank)

    return added