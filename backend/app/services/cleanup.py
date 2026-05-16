from typing import Any

from app.core.paths import REFERENCES_DIR, TEXTS_DIR, UPLOADS_DIR
from app.services.storage import (
    load_index,
    load_knowledge_forest,
    load_question_bank,
    save_index,
    save_knowledge_forest,
    save_question_bank,
)


def get_question_material_id(question: dict[str, Any]) -> str | None:
    material_id = question.get("source_material_id") or question.get("source_document_id")
    return str(material_id) if material_id else None


def get_question_tree_id(question: dict[str, Any]) -> str | None:
    tree_id = question.get("tree_id")
    return str(tree_id) if tree_id else None


def get_question_node_id(question: dict[str, Any]) -> str | None:
    node_id = question.get("node_id")
    return str(node_id) if node_id else None


def get_question_leaf_id(question: dict[str, Any]) -> str | None:
    leaf_id = question.get("leaf_id")
    return str(leaf_id) if leaf_id else None


def question_has_valid_forest_location(question: dict[str, Any], forest: dict[str, Any]) -> bool:
    tree_id = get_question_tree_id(question)
    node_id = get_question_node_id(question)
    leaf_id = get_question_leaf_id(question)

    if not tree_id and not node_id and not leaf_id:
        return True

    tree = forest.get("trees", {}).get(tree_id) if tree_id else None
    if not tree:
        return False

    node = tree.get("nodes", {}).get(node_id) if node_id else None
    if not node:
        return False

    leaf = node.get("leaves", {}).get(leaf_id) if leaf_id else None
    return bool(leaf)


def material_upload_exists(metadata: dict[str, Any]) -> bool:
    stored_filename = metadata.get("stored_filename")
    return bool(stored_filename and (UPLOADS_DIR / str(stored_filename)).exists())


def cleanup_orphan_questions(index: dict[str, Any], forest: dict[str, Any], questions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    valid_material_ids = set(index.keys())
    cleaned_questions = []

    for question in questions:
        material_id = get_question_material_id(question)
        if not material_id or material_id not in valid_material_ids:
            continue
        if not question_has_valid_forest_location(question, forest):
            continue
        cleaned_questions.append(question)

    return cleaned_questions, len(questions) - len(cleaned_questions)


def cleanup_orphan_reference_files(index: dict[str, Any]) -> int:
    valid_material_ids = set(index.keys())
    removed = 0
    if not REFERENCES_DIR.exists():
        return 0
    for path in REFERENCES_DIR.glob("*.json"):
        if path.stem not in valid_material_ids:
            path.unlink()
            removed += 1
    return removed


def cleanup_orphan_text_files(index: dict[str, Any]) -> int:
    valid_material_ids = set(index.keys())
    removed = 0
    if not TEXTS_DIR.exists():
        return 0
    for path in TEXTS_DIR.glob("*.txt"):
        if path.stem not in valid_material_ids:
            path.unlink()
            removed += 1
    return removed


def cleanup_orphan_upload_files(index: dict[str, Any]) -> int:
    valid_filenames = {str(metadata.get("stored_filename")) for metadata in index.values() if metadata.get("stored_filename")}
    removed = 0
    if not UPLOADS_DIR.exists():
        return 0
    for path in UPLOADS_DIR.iterdir():
        if path.is_file() and path.name not in valid_filenames:
            path.unlink()
            removed += 1
    return removed


def cleanup_orphan_materials(index: dict[str, Any], questions: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
    question_material_ids = {m for m in (get_question_material_id(q) for q in questions) if m}
    cleaned_index = {}
    removed = 0
    for material_id, metadata in index.items():
        upload_exists = material_upload_exists(metadata)
        text_exists = (TEXTS_DIR / f"{material_id}.txt").exists()
        references_exist = (REFERENCES_DIR / f"{material_id}.json").exists()
        has_questions = material_id in question_material_ids
        if upload_exists or text_exists or references_exist or has_questions:
            cleaned_index[material_id] = metadata
        else:
            removed += 1
    return cleaned_index, removed


def leaf_has_questions(leaf_id: str, questions: list[dict[str, Any]]) -> bool:
    return any(get_question_leaf_id(question) == leaf_id for question in questions)


def count_questions_for_leaf(leaf_id: str, questions: list[dict[str, Any]]) -> int:
    return sum(1 for question in questions if get_question_leaf_id(question) == leaf_id)


def cleanup_orphan_forest_nodes(forest: dict[str, Any], index: dict[str, Any], questions: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, int]]:
    valid_material_ids = set(index.keys())
    stats = {"removed_trees": 0, "removed_nodes": 0, "removed_leaves": 0, "trimmed_leaf_material_refs": 0}
    trees = forest.get("trees", {})
    if not isinstance(trees, dict):
        forest["trees"] = {}
        return forest, stats

    tree_ids_to_delete = []
    for tree_id, tree in list(trees.items()):
        nodes = tree.get("nodes", {})
        if not isinstance(nodes, dict):
            tree["nodes"] = {}
            nodes = tree["nodes"]
        node_ids_to_delete = []
        for node_id, node in list(nodes.items()):
            leaves = node.get("leaves", {})
            if not isinstance(leaves, dict):
                node["leaves"] = {}
                leaves = node["leaves"]
            leaf_ids_to_delete = []
            for leaf_id, leaf in list(leaves.items()):
                materials = leaf.get("materials", [])
                if not isinstance(materials, list): materials = []
                cleaned_materials = [m for m in materials if str(m) in valid_material_ids]
                stats["trimmed_leaf_material_refs"] += len(materials) - len(cleaned_materials)
                leaf["materials"] = cleaned_materials
                leaf["question_count"] = count_questions_for_leaf(leaf_id, questions)
                if not cleaned_materials and not leaf_has_questions(leaf_id, questions):
                    leaf_ids_to_delete.append(leaf_id)
            for leaf_id in leaf_ids_to_delete:
                del leaves[leaf_id]
                stats["removed_leaves"] += 1
            if not leaves:
                node_ids_to_delete.append(node_id)
        for node_id in node_ids_to_delete:
            del nodes[node_id]
            stats["removed_nodes"] += 1
        if not nodes:
            tree_ids_to_delete.append(tree_id)
    for tree_id in tree_ids_to_delete:
        del trees[tree_id]
        stats["removed_trees"] += 1
    forest["trees"] = trees
    return forest, stats


def clear_missing_forest_locations_from_materials(index: dict[str, Any], forest: dict[str, Any]) -> tuple[dict[str, Any], int]:
    trees = forest.get("trees", {})
    cleaned = 0
    for metadata in index.values():
        tree_id = metadata.get("tree_id")
        node_id = metadata.get("node_id")
        leaf_id = metadata.get("leaf_id")
        tree = trees.get(tree_id) if tree_id else None
        node = tree.get("nodes", {}).get(node_id) if tree and node_id else None
        leaf = node.get("leaves", {}).get(leaf_id) if node and leaf_id else None
        if tree_id and not leaf:
            metadata["tree_id"] = None
            metadata["tree_name"] = None
            metadata["node_id"] = None
            metadata["node_name"] = None
            metadata["leaf_id"] = None
            metadata["leaf_name"] = None
            metadata["knowledge_path"] = None
            cleaned += 1
    return index, cleaned


def cleanup_orphans() -> dict[str, Any]:
    index = load_index()
    forest = load_knowledge_forest()
    questions = load_question_bank()
    questions, removed_questions = cleanup_orphan_questions(index, forest, questions)
    index, removed_materials = cleanup_orphan_materials(index, questions)
    questions, removed_questions_second_pass = cleanup_orphan_questions(index, forest, questions)
    removed_questions += removed_questions_second_pass
    removed_reference_files = cleanup_orphan_reference_files(index)
    removed_text_files = cleanup_orphan_text_files(index)
    removed_upload_files = cleanup_orphan_upload_files(index)
    forest, forest_stats = cleanup_orphan_forest_nodes(forest, index, questions)
    index, cleaned_material_forest_locations = clear_missing_forest_locations_from_materials(index, forest)
    save_index(index)
    save_question_bank(questions)
    save_knowledge_forest(forest)
    return {
        "removed_materials": removed_materials,
        "removed_questions": removed_questions,
        "removed_reference_files": removed_reference_files,
        "removed_text_files": removed_text_files,
        "removed_upload_files": removed_upload_files,
        "removed_trees": forest_stats["removed_trees"],
        "removed_nodes": forest_stats["removed_nodes"],
        "removed_leaves": forest_stats["removed_leaves"],
        "trimmed_leaf_material_refs": forest_stats["trimmed_leaf_material_refs"],
        "cleaned_material_forest_locations": cleaned_material_forest_locations,
    }
