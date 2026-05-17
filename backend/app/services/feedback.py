from collections import defaultdict
from typing import Any

from fastapi import HTTPException

from app.services.ai import call_ai_json


def normalize_answer_value(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        clean = value.strip().upper()

        if clean in ["0", "1", "2", "3"]:
            return int(clean)

        if clean in ["A", "B", "C", "D"]:
            return ["A", "B", "C", "D"].index(clean)

    return None


def get_user_answer_for_question(answers: dict[str, Any], question: dict[str, Any], index: int) -> int | None:
    possible_keys = [
        str(question.get("question_id")),
        str(question.get("id")),
        str(index),
    ]

    for key in possible_keys:
        if key and key in answers:
            return normalize_answer_value(answers[key])

    return None


def calculate_exam_breakdown(questions: list[dict[str, Any]], answers: dict[str, Any]) -> dict[str, Any]:
    if not questions:
        raise HTTPException(
            status_code=400,
            detail="No se recibieron preguntas para analizar.",
        )

    total = len(questions)
    correct = 0
    wrong_questions = []
    area_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    leaf_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for index, question in enumerate(questions):
        correct_answer = normalize_answer_value(question.get("answer"))
        user_answer = get_user_answer_for_question(answers, question, index)
        is_correct = user_answer is not None and correct_answer is not None and user_answer == correct_answer

        area = question.get("area") or "Área no definida"
        leaf = question.get("leaf_name") or question.get("subarea") or "Tema no definido"

        area_stats[area]["total"] += 1
        leaf_stats[leaf]["total"] += 1

        if is_correct:
            correct += 1
            area_stats[area]["correct"] += 1
            leaf_stats[leaf]["correct"] += 1
        else:
            wrong_questions.append(
                {
                    "question_id": question.get("question_id"),
                    "q": question.get("q"),
                    "area": area,
                    "subarea": question.get("subarea"),
                    "leaf_name": question.get("leaf_name"),
                    "knowledge_path": question.get("knowledge_path"),
                    "source_document_name": question.get("source_document_name"),
                    "source_page": question.get("source_page"),
                    "source_excerpt": question.get("source_excerpt"),
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "options": question.get("options", []),
                }
            )

    return {
        "total": total,
        "correct": correct,
        "incorrect": total - correct,
        "percentage": round((correct / total) * 100, 2),
        "area_stats": dict(area_stats),
        "leaf_stats": dict(leaf_stats),
        "wrong_questions": wrong_questions,
    }


def compact_wrong_questions_for_prompt(wrong_questions: list[dict[str, Any]], limit: int = 20) -> str:
    if not wrong_questions:
        return "No hubo preguntas incorrectas."

    lines = []

    for item in wrong_questions[:limit]:
        lines.append(
            f"""
Pregunta: {item.get("q")}
Área: {item.get("area")}
Tema: {item.get("leaf_name") or item.get("subarea")}
Ruta: {item.get("knowledge_path")}
Respuesta del usuario: {item.get("user_answer")}
Respuesta correcta: {item.get("correct_answer")}
Extracto fuente: {item.get("source_excerpt")}
""".strip()
        )

    return "\\n\\n".join(lines)


def generate_exam_feedback(questions: list[dict[str, Any]], answers: dict[str, Any]) -> dict[str, Any]:
    breakdown = calculate_exam_breakdown(questions, answers)

    prompt = f"""
Analiza el resultado de un examen y genera retroalimentación útil para estudiar.

Resultado:
Total: {breakdown["total"]}
Correctas: {breakdown["correct"]}
Incorrectas: {breakdown["incorrect"]}
Porcentaje: {breakdown["percentage"]}

Estadísticas por área:
{breakdown["area_stats"]}

Estadísticas por tema:
{breakdown["leaf_stats"]}

Preguntas incorrectas:
{compact_wrong_questions_for_prompt(breakdown["wrong_questions"])}

Reglas:
- Responde en español.
- No exageres si el resultado fue bueno.
- Si el usuario tuvo muy buen resultado, da recomendaciones ligeras.
- Si falló mucho en un área, identifica esa área claramente.
- Si se repiten errores en el mismo tema, menciónalo.
- Da consejos concretos y estudiables.
- Responde únicamente JSON válido.

Formato:
{{
  "summary": "Resumen breve del desempeño",
  "performance_level": "alto | medio | bajo",
  "weak_areas": [
    {{
      "area": "Nombre del área",
      "reason": "Por qué debe mejorar aquí",
      "priority": "alta | media | baja"
    }}
  ],
  "recommended_actions": [
    "Consejo concreto 1",
    "Consejo concreto 2"
  ],
  "study_plan": [
    {{
      "step": 1,
      "task": "Actividad de estudio sugerida"
    }}
  ],
  "encouragement": "Mensaje final breve"
}}
""".strip()

    parsed = call_ai_json(
        system_message="Eres un tutor académico que analiza resultados de exámenes y da recomendaciones de mejora. Respondes únicamente JSON válido.",
        user_message=prompt,
        temperature=0.3,
    )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail="La retroalimentación generada no tiene formato válido.",
        )

    return {
        "score": {
            "total": breakdown["total"],
            "correct": breakdown["correct"],
            "incorrect": breakdown["incorrect"],
            "percentage": breakdown["percentage"],
        },
        "area_stats": breakdown["area_stats"],
        "leaf_stats": breakdown["leaf_stats"],
        "wrong_questions": breakdown["wrong_questions"],
        "feedback": parsed,
    }
