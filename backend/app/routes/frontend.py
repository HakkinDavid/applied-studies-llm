from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.paths import FRONTEND_BUILD


router = APIRouter()


@router.get("/", include_in_schema=False)
def serve_frontend_root():
    index_file = FRONTEND_BUILD / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return {
        "message": "Backend funcionando. Frontend todavía no compilado.",
        "api_docs": "/docs",
        "question_bank_js": "/egel/banco_preguntas.js",
        "question_bank_json": "/api/question-bank",
        "knowledge_forest": "/api/knowledge-forest",
        "health": "/api/health",
    }


@router.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(
            status_code=404,
            detail="Ruta API no encontrada.",
        )

    requested_file = FRONTEND_BUILD / full_path

    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)

    index_file = FRONTEND_BUILD / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(
        status_code=404,
        detail="Frontend no compilado.",
    )
