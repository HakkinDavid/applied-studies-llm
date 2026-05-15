from typing import Any

from fastapi import HTTPException

from app.core.paths import REFERENCES_DIR, TEXTS_DIR, UPLOADS_DIR
from app.services.cleanup import cleanup_orphans
from app.services.storage import load_index, load_knowledge_forest, load_question_bank, save_index, save_knowledge_forest, save_question_bank


def delete_material_by_id(material_id: str) -> dict[str, Any]:
    index = load_index()
    if material_id not in index:
        raise HTTPException(status_code=404, detail="Material no encontrado.")
    metadata = index[material_id]
    stored_filename = metadata.get("stored_filename")
    uploaded_path = UPLOADS_DIR / str(stored_filename) if stored_filename else None
    text_path = TEXTS_DIR / f"{material_id}.txt"
    references_path = REFERENCES_DIR / f"{material_id}.json"
    removed_files = []
    if uploaded_path and uploaded_path.exists():
        uploaded_path.unlink(); removed_files.append(str(uploaded_path.name))
    if text_path.exists():
        text_path.unlink(); removed_files.append(str(text_path.name))
    if references_path.exists():
        references_path.unlink(); removed_files.append(str(references_path.name))
    del index[material_id]
    save_index(index)
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "material", "id": material_id, "removed_files": removed_files, "cleanup": cleanup}


def delete_questions_without_immediate_cleanup(field: str, value: str) -> dict[str, Any]:
    questions = load_question_bank()
    kept_questions = []
    removed_questions = []
    for question in questions:
        if str(question.get(field)) == str(value):
            removed_questions.append(question)
        else:
            kept_questions.append(question)
    save_question_bank(kept_questions)
    return {"removed_questions": len(removed_questions)}


def delete_questions_by_filter(field: str, value: str) -> dict[str, Any]:
    result = delete_questions_without_immediate_cleanup(field, value)
    if result["removed_questions"] == 0:
        raise HTTPException(status_code=404, detail=f"No se encontraron preguntas con {field}={value}.")
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "questions", "field": field, "value": value, "removed_questions": result["removed_questions"], "cleanup": cleanup}


def delete_question_by_index(index_value: int) -> dict[str, Any]:
    questions = load_question_bank()
    if index_value < 0 or index_value >= len(questions):
        raise HTTPException(status_code=404, detail="No existe una pregunta con ese índice.")
    removed_question = questions.pop(index_value)
    save_question_bank(questions)
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "question", "index": index_value, "removed_question": removed_question, "cleanup": cleanup}


def delete_question_by_id(question_id: str) -> dict[str, Any]:
    questions = load_question_bank()
    kept_questions = []
    removed_question = None
    for question in questions:
        if str(question.get("question_id")) == str(question_id):
            removed_question = question
        else:
            kept_questions.append(question)
    if removed_question is None:
        raise HTTPException(status_code=404, detail="No existe una pregunta con ese question_id.")
    save_question_bank(kept_questions)
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "question", "question_id": question_id, "removed_question": removed_question, "cleanup": cleanup}


def delete_tree_by_id(tree_id: str) -> dict[str, Any]:
    forest = load_knowledge_forest()
    trees = forest.get("trees", {})
    if tree_id not in trees:
        raise HTTPException(status_code=404, detail="Árbol no encontrado.")
    removed_tree = trees.pop(tree_id)
    forest["trees"] = trees
    save_knowledge_forest(forest)
    questions_result = delete_questions_without_immediate_cleanup("tree_id", tree_id)
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "tree", "id": tree_id, "removed_tree_name": removed_tree.get("name"), "removed_questions": questions_result["removed_questions"], "cleanup": cleanup}


def delete_node_by_id(tree_id: str, node_id: str) -> dict[str, Any]:
    forest = load_knowledge_forest()
    trees = forest.get("trees", {})
    tree = trees.get(tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Árbol no encontrado.")
    nodes = tree.get("nodes", {})
    if node_id not in nodes:
        raise HTTPException(status_code=404, detail="Nodo no encontrado.")
    removed_node = nodes.pop(node_id)
    tree["nodes"] = nodes
    forest["trees"] = trees
    save_knowledge_forest(forest)
    questions_result = delete_questions_without_immediate_cleanup("node_id", node_id)
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "node", "tree_id": tree_id, "node_id": node_id, "removed_node_name": removed_node.get("name"), "removed_questions": questions_result["removed_questions"], "cleanup": cleanup}


def delete_leaf_by_id(tree_id: str, node_id: str, leaf_id: str) -> dict[str, Any]:
    forest = load_knowledge_forest()
    trees = forest.get("trees", {})
    tree = trees.get(tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Árbol no encontrado.")
    nodes = tree.get("nodes", {})
    node = nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado.")
    leaves = node.get("leaves", {})
    if leaf_id not in leaves:
        raise HTTPException(status_code=404, detail="Hoja no encontrada.")
    removed_leaf = leaves.pop(leaf_id)
    node["leaves"] = leaves
    tree["nodes"] = nodes
    forest["trees"] = trees
    save_knowledge_forest(forest)
    questions_result = delete_questions_without_immediate_cleanup("leaf_id", leaf_id)
    cleanup = cleanup_orphans()
    return {"status": "deleted", "type": "leaf", "tree_id": tree_id, "node_id": node_id, "leaf_id": leaf_id, "removed_leaf_name": removed_leaf.get("name"), "removed_questions": questions_result["removed_questions"], "cleanup": cleanup}
