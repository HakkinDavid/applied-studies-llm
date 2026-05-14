from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.materials import router as materials_router
from app.routes.questions import router as questions_router
from app.routes.forest import router as forest_router
from app.routes.frontend import router as frontend_router


app = FastAPI(
    title="Applied LLM Backend",
    description="Backend para subir material de estudio, construir un bosque de conocimiento y generar banco de preguntas con referencias.",
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

app.include_router(health_router)
app.include_router(materials_router)
app.include_router(questions_router)
app.include_router(forest_router)
app.include_router(frontend_router)
