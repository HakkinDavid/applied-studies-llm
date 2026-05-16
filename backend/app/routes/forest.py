from fastapi import APIRouter

from app.models.schemas import KnowledgeForestResponse
from app.services.areas import get_dynamic_areas
from app.services.cleanup import cleanup_orphans
from app.services.deletion import delete_leaf_by_id, delete_node_by_id, delete_tree_by_id
from app.services.storage import load_knowledge_forest, save_knowledge_forest


router = APIRouter()


@router.get("/api/areas")
def get_available_areas():
    areas = get_dynamic_areas()

    return {
        "total": len(areas),
        "areas": areas,
    }


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
    cleanup = cleanup_orphans()

    return {
        "status": "ok",
        "message": "Bosque de conocimiento borrado.",
        "cleanup": cleanup,
    }


@router.post("/api/cleanup/orphans")
def run_orphan_cleanup():
    cleanup = cleanup_orphans()

    return {
        "status": "ok",
        "message": "Limpieza de huérfanos ejecutada.",
        "cleanup": cleanup,
    }


@router.delete("/api/knowledge-forest/trees/{tree_id}")
def delete_tree(tree_id: str):
    return delete_tree_by_id(tree_id)


@router.delete("/api/knowledge-forest/trees/{tree_id}/nodes/{node_id}")
def delete_node(tree_id: str, node_id: str):
    return delete_node_by_id(tree_id, node_id)


@router.delete("/api/knowledge-forest/trees/{tree_id}/nodes/{node_id}/leaves/{leaf_id}")
def delete_leaf(tree_id: str, node_id: str, leaf_id: str):
    return delete_leaf_by_id(tree_id, node_id, leaf_id)