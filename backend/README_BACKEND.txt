BACKEND MODULAR - APPLIED STUDIES LLM


Estructura:
backend/
├── main.py
├── main.txt
├── requirements.txt
├── .env.example
├── .gitignore
└── app/
    ├── core/
    │   ├── config.py
    │   ├── config.txt
    │   ├── paths.py
    │   └── paths.txt
    ├── models/
    │   ├── schemas.py
    │   └── schemas.txt
    ├── services/
    │   ├── ai.py
    │   ├── ai.txt
    │   ├── files.py
    │   ├── files.txt
    │   ├── forest.py
    │   ├── forest.txt
    │   ├── materials.py
    │   ├── materials.txt
    │   ├── questions.py
    │   ├── questions.txt
    │   ├── storage.py
    │   ├── storage.txt
    │   ├── text.py
    │   ├── text.txt
    │   ├── utils.py
    │   └── utils.txt
    └── routes/


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
