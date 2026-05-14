from typing import Any, Optional

from fastapi import HTTPException

from app.core.config import FRONTEND_COMPATIBLE_AREAS
from app.services.ai import call_ai_json
from app.services.storage import load_knowledge_forest, save_knowledge_forest
from app.services.text import limit_text_for_generation
from app.services.utils import now_iso, slugify


def normalize_frontend_area(area: Any) -> str:
    if isinstance(area, str) and area in FRONTEND_COMPATIBLE_AREAS:
        return area

    return "Soluciones de cómputo inteligente"


def summarize_forest_for_prompt(forest: dict[str, Any], max_chars: int = 9000) -> str:
    trees = forest.get("trees", {})
    lines = []

    for tree in trees.values():
        lines.append(f"- Árbol: {tree.get('name', 'Sin nombre')}")
        description = tree.get("description", "")
        if description:
            lines.append(f"  Descripción: {description}")

        for node in tree.get("nodes", {}).values():
            lines.append(f"  - Nodo: {node.get('name', 'Sin nombre')}")
            node_description = node.get("description", "")
            if node_description:
                lines.append(f"    Descripción: {node_description}")

            for leaf in node.get("leaves", {}).values():
                lines.append(f"    - Hoja: {leaf.get('name', 'Sin nombre')}")
                leaf_description = leaf.get("description", "")
                if leaf_description:
                    lines.append(f"      Descripción: {leaf_description}")

    summary = "\n".join(lines).strip()

    if not summary:
        return "El bosque de conocimiento todavía está vacío."

    return limit_text_for_generation(summary, max_chars=max_chars)


def build_knowledge_classification_prompt(
    text: str,
    forest: dict[str, Any],
    tree_hint: Optional[str],
) -> str:
    frontend_areas = ", ".join(FRONTEND_COMPATIBLE_AREAS)
    forest_summary = summarize_forest_for_prompt(forest)
    hint_text = tree_hint.strip() if tree_hint and tree_hint.strip() else "No se proporcionó pista."

    return f"""
Analiza el material de estudio y clasifícalo dentro de un bosque de conocimiento.

Concepto del sistema:
- El bosque contiene varios árboles.
- Cada árbol representa una carrera, especialidad o dominio amplio de conocimiento.
- Cada árbol contiene nodos.
- Cada nodo representa un área importante dentro de esa carrera o especialidad.
- Cada nodo contiene hojas.
- Cada hoja representa un tema concreto o subtema evaluable.
- Si el material encaja con un árbol, nodo u hoja existente, reutilízalo.
- Si el material no encaja bien con lo existente, crea un nuevo árbol, nodo u hoja.
- Las áreas deben derivarse del conocimiento que ya existe dentro del árbol seleccionado.

Pista opcional del usuario:
{hint_text}

Bosque actual:
{forest_summary}

Además, por compatibilidad con el frontend actual, elige una categoría general de esta lista:
{frontend_areas}

Responde únicamente con JSON válido:
{{
  "tree_name": "Carrera o especialidad",
  "tree_description": "Descripción breve del árbol",
  "node_name": "Área derivada del árbol",
  "node_description": "Descripción breve del nodo",
  "leaf_name": "Tema específico",
  "leaf_description": "Descripción breve de la hoja",
  "frontend_area": "Una categoría exacta de compatibilidad",
  "summary": "Resumen breve del material"
}}

Material:
{limit_text_for_generation(text, max_chars=14000)}
""".strip()


def classify_material_for_forest(
    text: str,
    forest: dict[str, Any],
    tree_hint: Optional[str] = None,
) -> dict[str, str]:
    prompt = build_knowledge_classification_prompt(text, forest, tree_hint)

    parsed = call_ai_json(
        system_message="Eres un clasificador académico. Respondes únicamente con JSON válido.",
        user_message=prompt,
        temperature=0.2,
    )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail="La clasificación generada por el modelo no tiene formato válido.",
        )

    return {
        "tree_name": str(parsed.get("tree_name") or "Conocimiento general").strip(),
        "tree_description": str(parsed.get("tree_description") or "").strip(),
        "node_name": str(parsed.get("node_name") or "Área general").strip(),
        "node_description": str(parsed.get("node_description") or "").strip(),
        "leaf_name": str(parsed.get("leaf_name") or "Tema general").strip(),
        "leaf_description": str(parsed.get("leaf_description") or "").strip(),
        "frontend_area": normalize_frontend_area(parsed.get("frontend_area")),
        "summary": str(parsed.get("summary") or "").strip(),
    }


def find_existing_tree_id(forest: dict[str, Any], tree_name: str) -> Optional[str]:
    normalized_name = tree_name.strip().lower()

    for tree_id, tree in forest.get("trees", {}).items():
        if tree.get("name", "").strip().lower() == normalized_name:
            return tree_id

    return None


def find_existing_node_id(tree: dict[str, Any], node_name: str) -> Optional[str]:
    normalized_name = node_name.strip().lower()

    for node_id, node in tree.get("nodes", {}).items():
        if node.get("name", "").strip().lower() == normalized_name:
            return node_id

    return None


def find_existing_leaf_id(node: dict[str, Any], leaf_name: str) -> Optional[str]:
    normalized_name = leaf_name.strip().lower()

    for leaf_id, leaf in node.get("leaves", {}).items():
        if leaf.get("name", "").strip().lower() == normalized_name:
            return leaf_id

    return None


def update_knowledge_forest(
    classification: dict[str, str],
    material_id: str,
    generated_questions: int = 0,
) -> dict[str, str]:
    forest = load_knowledge_forest()
    trees = forest["trees"]

    tree_name = classification["tree_name"]
    node_name = classification["node_name"]
    leaf_name = classification["leaf_name"]

    tree_id = find_existing_tree_id(forest, tree_name)

    if not tree_id:
        tree_id = slugify(tree_name)

        if tree_id in trees:
            tree_id = f"{tree_id}-{len(trees) + 1}"

        trees[tree_id] = {
            "id": tree_id,
            "name": tree_name,
            "description": classification.get("tree_description", ""),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "nodes": {},
        }

    tree = trees[tree_id]
    tree["updated_at"] = now_iso()

    if classification.get("tree_description") and not tree.get("description"):
        tree["description"] = classification["tree_description"]

    if "nodes" not in tree or not isinstance(tree["nodes"], dict):
        tree["nodes"] = {}

    node_id = find_existing_node_id(tree, node_name)

    if not node_id:
        node_id = slugify(node_name)

        if node_id in tree["nodes"]:
            node_id = f"{node_id}-{len(tree['nodes']) + 1}"

        tree["nodes"][node_id] = {
            "id": node_id,
            "name": node_name,
            "description": classification.get("node_description", ""),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "leaves": {},
        }

    node = tree["nodes"][node_id]
    node["updated_at"] = now_iso()

    if classification.get("node_description") and not node.get("description"):
        node["description"] = classification["node_description"]

    if "leaves" not in node or not isinstance(node["leaves"], dict):
        node["leaves"] = {}

    leaf_id = find_existing_leaf_id(node, leaf_name)

    if not leaf_id:
        leaf_id = slugify(leaf_name)

        if leaf_id in node["leaves"]:
            leaf_id = f"{leaf_id}-{len(node['leaves']) + 1}"

        node["leaves"][leaf_id] = {
            "id": leaf_id,
            "name": leaf_name,
            "description": classification.get("leaf_description", ""),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "materials": [],
            "question_count": 0,
        }

    leaf = node["leaves"][leaf_id]
    leaf["updated_at"] = now_iso()

    if classification.get("leaf_description") and not leaf.get("description"):
        leaf["description"] = classification["leaf_description"]

    if "materials" not in leaf or not isinstance(leaf["materials"], list):
        leaf["materials"] = []

    if material_id not in leaf["materials"]:
        leaf["materials"].append(material_id)

    leaf["question_count"] = int(leaf.get("question_count", 0)) + generated_questions

    save_knowledge_forest(forest)

    return {
        "tree_id": tree_id,
        "tree_name": tree["name"],
        "node_id": node_id,
        "node_name": node["name"],
        "leaf_id": leaf_id,
        "leaf_name": leaf["name"],
        "knowledge_path": f"{tree['name']} > {node['name']} > {leaf['name']}",
    }
