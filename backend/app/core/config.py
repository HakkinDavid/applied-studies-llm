import os

from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
MODEL = os.getenv("MODEL", "")

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

MAX_REFERENCE_CHARS = 420
MAX_REFERENCES_FOR_PROMPT = 45
