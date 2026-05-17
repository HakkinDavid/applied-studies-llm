from fastapi import APIRouter

from app.core.config import MODEL, OPENAI_BASE_URL
from app.services.ai import is_ai_configured


router = APIRouter()


@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "Backend funcionando correctamente.",
        "ai_configured": is_ai_configured(),
        # "base_url": OPENAI_BASE_URL, # pasado de lanza rafa, como q exponiendo nuestros datos sensibles
        "model": MODEL,
    }
