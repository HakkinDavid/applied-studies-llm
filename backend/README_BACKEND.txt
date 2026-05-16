BACKEND MODULAR - APPLIED STUDIES LLM

Instalación:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

Crear .env:
OPENAI_BASE_URL=
OPENAI_API_KEY=
MODEL=
MAX_FILE_SIZE_MB=10
DEFAULT_QUESTION_COUNT=15

Ejecutar:
python -m uvicorn main:app --reload

Probar:
http://127.0.0.1:8000/docs
