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

## ¿Cómo usar?
1. Acceder a la URL
2. Verificar que el backend esté conectado
3. Cargar un documento de estudio relevante
4. Esperar a su procesamiento
5. Revisar el documento procesado y sus referencias
6. Tener una breve sesión de estudio previo a la evaluación
7. Solicitar una evaluación en el área de estudio deseada
8. Responder a las preguntas en el tiempo seleccionado
9. Obtener retroalimentación
10. Estudiar e iterar
