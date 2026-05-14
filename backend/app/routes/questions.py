import json

from fastapi import APIRouter, Response

from app.models.schemas import QuestionBankResponse
from app.services.storage import load_question_bank, save_question_bank


router = APIRouter()


@router.get("/api/question-bank", response_model=QuestionBankResponse)
def get_question_bank():
    questions = load_question_bank()

    return QuestionBankResponse(
        total=len(questions),
        questions=questions,
    )


@router.delete("/api/question-bank")
def clear_question_bank():
    save_question_bank([])

    return {
        "status": "ok",
        "message": "Banco de preguntas borrado.",
    }


@router.get("/egel/banco_preguntas.js")
def serve_question_bank_js():
    questions = load_question_bank()
    js = "window.questions = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";"

    return Response(
        content=js,
        media_type="application/javascript; charset=utf-8",
    )
