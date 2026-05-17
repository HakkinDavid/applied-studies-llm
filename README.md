# Applied Studies LLM
## Sistema en producción:
    Ir a https://asllm.bonsanbec.dev/

#### Alternativamente...
## Instalación del backend:
    cd backend/
    python -m venv venv
    venv\Scripts\activate o source venv/bin/activate
    pip install -r requirements.txt

###    Crear .env:
        OPENAI_BASE_URL=
        OPENAI_API_KEY=
        MODEL=
        MAX_FILE_SIZE_MB=10
        DEFAULT_QUESTION_COUNT=15

## Instalación del frontend:
    cd frontend/
    npm i
    npm run build

## Ejecutar sistema:
    python -m uvicorn main:app --reload

## Probar:
    Ir a http://127.0.0.1:8000/