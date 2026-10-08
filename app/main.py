from fastapi import FastAPI
from app.api.v1 import evaluaciones, grupos, academico, evaluadores, plantillas
from app.db.session import engine
from app.models.domain import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Evaluación de Proyectos CBA",
    description="Backend para la gestión y evaluación de proyectos formativos.",
    version="1.0.0"
)

app.include_router(academico.router, prefix="/api/v1")
app.include_router(grupos.router, prefix="/api/v1")
app.include_router(evaluadores.router, prefix="/api/v1")
app.include_router(plantillas.router, prefix="/api/v1")
app.include_router(evaluaciones.router, prefix="/api/v1")