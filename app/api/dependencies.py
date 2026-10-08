# app/api/dependencies.py
from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    Inyecta una sesión de base de datos en los endpoints de FastAPI.
    El uso de yield permite ejecutar el bloque 'finally' al terminar
    el request HTTP, evitando fugas de memoria o conexiones colgadas.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()