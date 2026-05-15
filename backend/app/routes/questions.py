import json

from fastapi import APIRouter, Response

from app.models.schemas import QuestionBankResponse
from app.services.cleanup import cleanup_orphans
from app.services.deletion import delete_question_by_id, delete_question_by_index, delete_questions_by_filter
from app.services.storage import load_question_bank, save_question_bank


router = APIRouter()


@router.get("/api/question-bank", response_model=QuestionBankResponse)
def get_question_bank():
    questions = load_question_bank()
    return QuestionBankResponse(total=len(questions), questions=questions)


@router.delete("/api/question-bank")
def clear_question_bank():
    save_question_bank([])
    cleanup = cleanup_orphans()
    return {"status": "ok", "message": "Banco de preguntas borrado.", "cleanup": cleanup}


@router.delete("/api/question-bank/index/{question_index}")
def delete_question_index(question_index: int):
    return delete_question_by_index(question_index)


@router.delete("/api/question-bank/question/{question_id}")
def delete_question_id(question_id: str):
    return delete_question_by_id(question_id)


@router.delete("/api/question-bank/by-material/{material_id}")
def delete_questions_by_material(material_id: str):
    return delete_questions_by_filter("source_material_id", material_id)


@router.delete("/api/question-bank/by-tree/{tree_id}")
def delete_questions_by_tree(tree_id: str):
    return delete_questions_by_filter("tree_id", tree_id)


@router.delete("/api/question-bank/by-node/{node_id}")
def delete_questions_by_node(node_id: str):
    return delete_questions_by_filter("node_id", node_id)


@router.delete("/api/question-bank/by-leaf/{leaf_id}")
def delete_questions_by_leaf(leaf_id: str):
    return delete_questions_by_filter("leaf_id", leaf_id)


@router.get("/egel/banco_preguntas.js")
def serve_question_bank_js():
    questions = load_question_bank()
    js = "window.questions = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";"
    return Response(content=js, media_type="application/javascript; charset=utf-8")
