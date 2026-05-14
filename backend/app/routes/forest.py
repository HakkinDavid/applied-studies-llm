from fastapi import APIRouter

from app.models.schemas import KnowledgeForestResponse
from app.services.storage import load_knowledge_forest, save_knowledge_forest


router = APIRouter()


@router.get("/api/knowledge-forest", response_model=KnowledgeForestResponse)
def get_knowledge_forest():
    forest = load_knowledge_forest()
    total_trees = len(forest.get("trees", {}))

    return KnowledgeForestResponse(
        total_trees=total_trees,
        forest=forest,
    )


@router.delete("/api/knowledge-forest")
def clear_knowledge_forest():
    save_knowledge_forest({"trees": {}})

    return {
        "status": "ok",
        "message": "Bosque de conocimiento borrado.",
    }
