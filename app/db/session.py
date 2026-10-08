# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Si la URL apunta a Supabase (contiene supabase.co o pooler.supabase.com)
# deshabilitamos NullPool o ajustamos pool_pre_ping para evitar conexiones colgadas.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Crucial en Supabase para descartar conexiones inactivas
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)