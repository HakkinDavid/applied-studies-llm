import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from docx import Document
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
TEXTS_DIR = STORAGE_DIR / "texts"
INDEX_FILE = STORAGE_DIR / "materials.json"
QUESTION_BANK_FILE = STORAGE_DIR / "question_bank.json"
KNOWLEDGE_FOREST_FILE = STORAGE_DIR / "knowledge_forest.json"

FRONTEND_BUILD = PROJECT_ROOT / "frontend" / "build"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)
MODEL = os.getenv("MODEL", "")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
) if OPENAI_API_KEY and OPENAI_BASE_URL and MODEL else None

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
DEFAULT_QUESTION_COUNT = int(os.getenv("DEFAULT_QUESTION_COUNT", "15"))

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

FRONTEND_COMPATIBLE_AREAS = [
    "Algoritmia",
    "Desarrollo de software de base",
    "Desarrollo de software de aplicación",
    "Soluciones de cómputo inteligente",
    "Lengua",
]

STORAGE_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
TEXTS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Applied LLM Backend",
    description="Backend para subir material de estudio, construir un bosque de conocimiento y generar banco de preguntas.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MaterialResponse(BaseModel):
    id: str
    sha256: str
    original_filename: str
    stored_filename: str
    extension: str
    content_type: Optional[str]
    size_bytes: int
    text_chars: int
    uploaded_at: str
    duplicate: bool
    generated_questions: int
    area: Optional[str] = None
    subarea: Optional[str] = None
    classification_summary: Optional[str] = None
    tree_id: Optional[str] = None
    tree_name: Optional[str] = None
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    leaf_id: Optional[str] = None
    leaf_name: Optional[str] = None
    knowledge_path: Optional[str] = None


class MaterialListResponse(BaseModel):
    total: int
    materials: list[dict[str, Any]]


class QuestionBankResponse(BaseModel):
    total: int
    questions: list[dict[str, Any]]


class KnowledgeForestResponse(BaseModel):
    total_trees: int
    forest: dict[str, Any]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_index() -> dict[str, Any]:
    return load_json(INDEX_FILE, {})


def save_index(index: dict[str, Any]) -> None:
    save_json(INDEX_FILE, index)


def load_question_bank() -> list[dict[str, Any]]:
    data = load_json(QUESTION_BANK_FILE, [])

    if not isinstance(data, list):
        return []

    return data


def save_question_bank(questions: list[dict[str, Any]]) -> None:
    save_json(QUESTION_BANK_FILE, questions)


def load_knowledge_forest() -> dict[str, Any]:
    forest = load_json(KNOWLEDGE_FOREST_FILE, {"trees": {}})

    if not isinstance(forest, dict):
        return {"trees": {}}

    if "trees" not in forest or not isinstance(forest["trees"], dict):
        forest["trees"] = {}

    return forest


def save_knowledge_forest(forest: dict[str, Any]) -> None:
    save_json(KNOWLEDGE_FOREST_FILE, forest)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")

    return value or "sin-nombre"


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_file(filename: str, data: bytes) -> str:
    extension = get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Formatos permitidos: {allowed}",
        )

    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío.",
        )

    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo supera el límite de {MAX_FILE_SIZE_MB} MB.",
        )

    return extension


def extract_text_from_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el PDF: {error}",
        )


def extract_text_from_docx(data: bytes) -> str:
    try:
        document = Document(BytesIO(data))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        return "\n".join(paragraphs)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el DOCX: {error}",
        )


def extract_text_from_plain_file(data: bytes) -> str:
    for encoding in ["utf-8", "latin-1"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass

    raise HTTPException(
        status_code=400,
        detail="No se pudo leer el archivo de texto.",
    )


def extract_text(data: bytes, extension: str) -> str:
    if extension == ".pdf":
        return extract_text_from_pdf(data)

    if extension == ".docx":
        return extract_text_from_docx(data)

    if extension in [".txt", ".md"]:
        return extract_text_from_plain_file(data)

    raise HTTPException(
        status_code=400,
        detail="No hay extractor disponible para este formato.",
    )


def clean_text(text: str) -> str:
    lines = []

    for line in text.splitlines():
        clean_line = line.strip()
        if clean_line:
            lines.append(clean_line)

    return "\n".join(lines)


def limit_text_for_generation(text: str, max_chars: int = 25000) -> str:
    if len(text) <= max_chars:
        return text

    start = text[: max_chars // 2]
    end = text[-max_chars // 2:]

    return start + "\n\n[...contenido omitido por longitud...]\n\n" + end


def extract_json_from_model_text(text: str) -> Any:
    clean = text.strip()

    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"```$", "", clean).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", clean, flags=re.DOTALL)

    if not match:
        raise HTTPException(
            status_code=500,
            detail="El modelo no devolvió JSON válido.",
        )

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="No se pudo interpretar el JSON generado por el modelo.",
        )


def ensure_ai_client() -> None:
    if not OPENAI_BASE_URL:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar OPENAI_BASE_URL en el archivo .env.",
        )

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar OPENAI_API_KEY en el archivo .env.",
        )

    if not MODEL:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar MODEL en el archivo .env.",
        )

    if client is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo inicializar el cliente de IA.",
        )


def normalize_answer(answer: Any) -> int:
    if isinstance(answer, int) and 0 <= answer <= 3:
        return answer

    if isinstance(answer, str):
        value = answer.strip().upper()

        if value in ["0", "1", "2", "3"]:
            return int(value)

        if value in ["A", "B", "C", "D"]:
            return ["A", "B", "C", "D"].index(value)

    return 0


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

        nodes = tree.get("nodes", {})

        for node in nodes.values():
            lines.append(f"  - Nodo: {node.get('name', 'Sin nombre')}")
            node_description = node.get("description", "")
            if node_description:
                lines.append(f"    Descripción: {node_description}")

            leaves = node.get("leaves", {})

            for leaf in leaves.values():
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
- No fuerces una clasificación si otra nueva es más clara.

Pista opcional proporcionada por el usuario:
{hint_text}

Bosque actual:
{forest_summary}

Además, por compatibilidad con el frontend actual, debes elegir una categoría técnica general de esta lista:
{frontend_areas}

Responde únicamente con JSON válido usando este formato exacto:
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

Reglas:
- No uses markdown.
- No agregues texto fuera del JSON.
- "tree_name" debe ser una carrera, especialidad o dominio amplio.
- "node_name" debe ser un área que tenga sentido dentro del árbol.
- "leaf_name" debe ser un tema específico y evaluable.
- "frontend_area" debe ser exactamente uno de los valores permitidos de compatibilidad.
- Si el bosque actual está vacío, crea la primera estructura con base en el material.
- Si ya existe una estructura compatible, reutiliza nombres similares en lugar de crear duplicados.
- Usa nombres claros, cortos y académicos.

Material:
{limit_text_for_generation(text, max_chars=14000)}
""".strip()


def classify_material_for_forest(
    text: str,
    forest: dict[str, Any],
    tree_hint: Optional[str] = None,
) -> dict[str, str]:
    ensure_ai_client()

    prompt = build_knowledge_classification_prompt(
        text=text,
        forest=forest,
        tree_hint=tree_hint,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un clasificador académico. Respondes únicamente con JSON válido.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al clasificar el material con IA: {error}",
        )

    content = response.choices[0].message.content

    if not content:
        raise HTTPException(
            status_code=500,
            detail="El modelo respondió vacío al clasificar el material.",
        )

    parsed = extract_json_from_model_text(content)

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail="La clasificación generada por el modelo no tiene formato válido.",
        )

    tree_name = str(parsed.get("tree_name") or "Conocimiento general").strip()
    node_name = str(parsed.get("node_name") or "Área general").strip()
    leaf_name = str(parsed.get("leaf_name") or "Tema general").strip()

    tree_description = str(parsed.get("tree_description") or "").strip()
    node_description = str(parsed.get("node_description") or "").strip()
    leaf_description = str(parsed.get("leaf_description") or "").strip()
    summary = str(parsed.get("summary") or "").strip()
    frontend_area = normalize_frontend_area(parsed.get("frontend_area"))

    return {
        "tree_name": tree_name,
        "tree_description": tree_description,
        "node_name": node_name,
        "node_description": node_description,
        "leaf_name": leaf_name,
        "leaf_description": leaf_description,
        "frontend_area": frontend_area,
        "summary": summary,
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


def normalize_question(
    raw_question: dict[str, Any],
    material_id: str,
    frontend_area: str,
    subarea: str,
    forest_location: dict[str, str],
) -> Optional[dict[str, Any]]:
    q = str(raw_question.get("q") or raw_question.get("question") or "").strip()
    options = raw_question.get("options")

    if not q or not isinstance(options, list) or len(options) != 4:
        return None

    clean_options = [str(option).strip() for option in options]

    if any(not option for option in clean_options):
        return None

    return {
        "q": q,
        "options": clean_options,
        "answer": normalize_answer(raw_question.get("answer")),
        "area": normalize_frontend_area(raw_question.get("area") or frontend_area),
        "subarea": str(raw_question.get("subarea") or subarea).strip(),
        "synthetic": True,
        "source_material_id": material_id,
        "tree_id": forest_location["tree_id"],
        "tree_name": forest_location["tree_name"],
        "node_id": forest_location["node_id"],
        "node_name": forest_location["node_name"],
        "leaf_id": forest_location["leaf_id"],
        "leaf_name": forest_location["leaf_name"],
        "knowledge_path": forest_location["knowledge_path"],
    }


def build_question_generation_prompt(
    text: str,
    num_questions: int,
    frontend_area: str,
    forest_location: dict[str, str],
) -> str:
    frontend_areas = ", ".join(FRONTEND_COMPATIBLE_AREAS)

    return f"""
Genera un banco de preguntas para un simulador de examen.

Debes basarte únicamente en el material proporcionado.
No inventes conceptos que no estén relacionados con el documento.
Genera exactamente {num_questions} preguntas.
Todas deben ser de opción múltiple.
Cada pregunta debe tener exactamente 4 opciones.
La respuesta correcta debe indicarse como número entero usando estos índices:
0 para la primera opción,
1 para la segunda opción,
2 para la tercera opción,
3 para la cuarta opción.

Ubicación del material en el bosque de conocimiento:
Árbol: {forest_location["tree_name"]}
Nodo: {forest_location["node_name"]}
Hoja: {forest_location["leaf_name"]}
Ruta: {forest_location["knowledge_path"]}

El frontend espera este formato exacto:
[
  {{
    "q": "Texto de la pregunta",
    "options": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
    "answer": 0,
    "area": "Soluciones de cómputo inteligente",
    "subarea": "Tema específico",
    "synthetic": true
  }}
]

Reglas:
- Responde solamente con JSON válido.
- No uses markdown.
- No agregues explicaciones fuera del JSON.
- El campo "q" debe contener la pregunta.
- El campo "options" debe contener 4 respuestas posibles.
- El campo "answer" debe ser un número de 0 a 3.
- El campo "synthetic" siempre debe ser true.
- El campo "area" debe ser uno de estos valores exactos: {frontend_areas}.
- Para compatibilidad, usa preferentemente esta area: {frontend_area}.
- El campo "subarea" debe relacionarse con la hoja del bosque: {forest_location["leaf_name"]}.
- Las preguntas deben evaluar comprensión, no solo memorización literal.
- Evita preguntas ambiguas.
- Evita opciones obviamente incorrectas.
- No menciones "según el documento" en cada pregunta.

Material:
{text}
""".strip()


def generate_questions_with_ai(
    text: str,
    material_id: str,
    num_questions: int,
    frontend_area: str,
    forest_location: dict[str, str],
) -> list[dict[str, Any]]:
    ensure_ai_client()

    prompt = build_question_generation_prompt(
        text=limit_text_for_generation(text),
        num_questions=num_questions,
        frontend_area=frontend_area,
        forest_location=forest_location,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un profesor que genera preguntas de examen. Respondes únicamente con JSON válido.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al comunicarse con el servicio de IA usando la librería de OpenAI: {error}",
        )

    content = response.choices[0].message.content

    if not content:
        raise HTTPException(
            status_code=500,
            detail="El modelo respondió vacío.",
        )

    parsed = extract_json_from_model_text(content)

    if isinstance(parsed, dict):
        raw_questions = parsed.get("questions", [])
    elif isinstance(parsed, list):
        raw_questions = parsed
    else:
        raw_questions = []

    normalized = []

    for raw_question in raw_questions:
        if isinstance(raw_question, dict):
            question = normalize_question(
                raw_question=raw_question,
                material_id=material_id,
                frontend_area=frontend_area,
                subarea=forest_location["leaf_name"],
                forest_location=forest_location,
            )

            if question:
                normalized.append(question)

    if not normalized:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron generar preguntas válidas.",
        )

    return normalized


def add_questions_to_bank(new_questions: list[dict[str, Any]]) -> int:
    bank = load_question_bank()

    existing_keys = {
        question.get("q", "").strip().lower()
        for question in bank
    }

    added = 0

    for question in new_questions:
        key = question.get("q", "").strip().lower()

        if key and key not in existing_keys:
            bank.append(question)
            existing_keys.add(key)
            added += 1

    save_question_bank(bank)

    return added


def build_material_metadata(
    sha256: str,
    original_filename: str,
    stored_filename: str,
    extension: str,
    content_type: Optional[str],
    size_bytes: int,
    text_chars: int,
    duplicate: bool,
    generated_questions: int,
    frontend_area: str,
    classification_summary: str,
    forest_location: dict[str, str],
) -> dict[str, Any]:
    return {
        "id": sha256,
        "sha256": sha256,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "extension": extension,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "text_chars": text_chars,
        "uploaded_at": now_iso(),
        "duplicate": duplicate,
        "generated_questions": generated_questions,
        "area": frontend_area,
        "subarea": forest_location["leaf_name"],
        "classification_summary": classification_summary,
        "tree_id": forest_location["tree_id"],
        "tree_name": forest_location["tree_name"],
        "node_id": forest_location["node_id"],
        "node_name": forest_location["node_name"],
        "leaf_id": forest_location["leaf_id"],
        "leaf_name": forest_location["leaf_name"],
        "knowledge_path": forest_location["knowledge_path"],
    }


def process_material_text(
    cleaned_text: str,
    sha256: str,
    num_questions: int,
    tree_hint: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int, str, str, dict[str, str]]:
    forest = load_knowledge_forest()

    classification = classify_material_for_forest(
        text=cleaned_text,
        forest=forest,
        tree_hint=tree_hint,
    )

    frontend_area = normalize_frontend_area(classification["frontend_area"])

    forest_location = update_knowledge_forest(
        classification=classification,
        material_id=sha256,
        generated_questions=0,
    )

    generated_questions = generate_questions_with_ai(
        text=cleaned_text,
        material_id=sha256,
        num_questions=num_questions,
        frontend_area=frontend_area,
        forest_location=forest_location,
    )

    added_questions = add_questions_to_bank(generated_questions)

    if added_questions > 0:
        update_knowledge_forest(
            classification=classification,
            material_id=sha256,
            generated_questions=added_questions,
        )

    return (
        generated_questions,
        added_questions,
        frontend_area,
        classification["summary"],
        forest_location,
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "Backend funcionando correctamente.",
        "ai_configured": client is not None,
        "base_url": OPENAI_BASE_URL,
        "model": MODEL,
    }


@app.post("/api/materials/upload", response_model=MaterialResponse)
async def upload_material(
    file: UploadFile = File(...),
    tree_hint: Optional[str] = Form(default=None),
    num_questions: int = Form(default=DEFAULT_QUESTION_COUNT),
):
    original_filename = file.filename or "archivo_sin_nombre"
    data = await file.read()

    extension = validate_file(original_filename, data)
    sha256 = calculate_sha256(data)

    stored_filename = f"{sha256}{extension}"
    stored_path = UPLOADS_DIR / stored_filename
    text_path = TEXTS_DIR / f"{sha256}.txt"

    index = load_index()
    duplicate = sha256 in index

    if num_questions < 1 or num_questions > 40:
        raise HTTPException(
            status_code=400,
            detail="El número de preguntas debe estar entre 1 y 40.",
        )

    if duplicate:
        metadata = dict(index[sha256])

        existing_questions = [
            question for question in load_question_bank()
            if question.get("source_material_id") == sha256
        ]

        if existing_questions:
            metadata["duplicate"] = True
            metadata["generated_questions"] = len(existing_questions)
            return MaterialResponse(**metadata)

        if not text_path.exists():
            raise HTTPException(
                status_code=409,
                detail="El archivo ya estaba registrado, pero no se encontró el texto extraído. Borra el material y vuelve a subirlo.",
            )

        with text_path.open("r", encoding="utf-8") as text_file:
            cleaned_text = text_file.read()

        _, added_questions, frontend_area, classification_summary, forest_location = process_material_text(
            cleaned_text=cleaned_text,
            sha256=sha256,
            num_questions=num_questions,
            tree_hint=tree_hint,
        )

        metadata["duplicate"] = True
        metadata["generated_questions"] = added_questions
        metadata["area"] = frontend_area
        metadata["subarea"] = forest_location["leaf_name"]
        metadata["classification_summary"] = classification_summary
        metadata["tree_id"] = forest_location["tree_id"]
        metadata["tree_name"] = forest_location["tree_name"]
        metadata["node_id"] = forest_location["node_id"]
        metadata["node_name"] = forest_location["node_name"]
        metadata["leaf_id"] = forest_location["leaf_id"]
        metadata["leaf_name"] = forest_location["leaf_name"]
        metadata["knowledge_path"] = forest_location["knowledge_path"]

        index[sha256] = metadata
        save_index(index)

        return MaterialResponse(**metadata)

    extracted_text = extract_text(data, extension)
    cleaned_text = clean_text(extracted_text)

    if len(cleaned_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="El archivo tiene muy poco texto útil para generar preguntas.",
        )

    _, added_questions, frontend_area, classification_summary, forest_location = process_material_text(
        cleaned_text=cleaned_text,
        sha256=sha256,
        num_questions=num_questions,
        tree_hint=tree_hint,
    )

    stored_path.write_bytes(data)

    with text_path.open("w", encoding="utf-8") as text_file:
        text_file.write(cleaned_text)

    metadata = build_material_metadata(
        sha256=sha256,
        original_filename=original_filename,
        stored_filename=stored_filename,
        extension=extension,
        content_type=file.content_type,
        size_bytes=len(data),
        text_chars=len(cleaned_text),
        duplicate=False,
        generated_questions=added_questions,
        frontend_area=frontend_area,
        classification_summary=classification_summary,
        forest_location=forest_location,
    )

    index[sha256] = metadata
    save_index(index)

    return MaterialResponse(**metadata)


@app.get("/api/materials", response_model=MaterialListResponse)
def list_materials():
    index = load_index()
    materials = list(index.values())
    materials.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)

    return MaterialListResponse(
        total=len(materials),
        materials=materials,
    )


@app.get("/api/question-bank", response_model=QuestionBankResponse)
def get_question_bank():
    questions = load_question_bank()

    return QuestionBankResponse(
        total=len(questions),
        questions=questions,
    )


@app.delete("/api/question-bank")
def clear_question_bank():
    save_question_bank([])

    return {
        "status": "ok",
        "message": "Banco de preguntas borrado.",
    }


@app.get("/api/knowledge-forest", response_model=KnowledgeForestResponse)
def get_knowledge_forest():
    forest = load_knowledge_forest()
    total_trees = len(forest.get("trees", {}))

    return KnowledgeForestResponse(
        total_trees=total_trees,
        forest=forest,
    )


@app.delete("/api/knowledge-forest")
def clear_knowledge_forest():
    save_knowledge_forest({"trees": {}})

    return {
        "status": "ok",
        "message": "Bosque de conocimiento borrado.",
    }


@app.get("/egel/banco_preguntas.js")
def serve_question_bank_js():
    questions = load_question_bank()
    js = "window.questions = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";"

    return Response(
        content=js,
        media_type="application/javascript; charset=utf-8",
    )


@app.get("/", include_in_schema=False)
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


@app.get("/{full_path:path}", include_in_schema=False)
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