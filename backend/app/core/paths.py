from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

STORAGE_DIR = BACKEND_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
TEXTS_DIR = STORAGE_DIR / "texts"
REFERENCES_DIR = STORAGE_DIR / "references"

INDEX_FILE = STORAGE_DIR / "materials.json"
QUESTION_BANK_FILE = STORAGE_DIR / "question_bank.json"
KNOWLEDGE_FOREST_FILE = STORAGE_DIR / "knowledge_forest.json"

FRONTEND_BUILD = PROJECT_ROOT / "frontend" / "build"


def ensure_storage_directories() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
    TEXTS_DIR.mkdir(exist_ok=True)
    REFERENCES_DIR.mkdir(exist_ok=True)


ensure_storage_directories()
