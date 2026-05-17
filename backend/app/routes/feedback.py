from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.feedback import generate_exam_feedback


router = APIRouter()


class ExamFeedbackRequest(BaseModel):
    questions: list[dict[str, Any]]
    answers: dict[str, Any]


@router.post("/api/exam/feedback")
def exam_feedback(payload: ExamFeedbackRequest):
    return generate_exam_feedback(
        questions=payload.questions,
        answers=payload.answers,
    )
