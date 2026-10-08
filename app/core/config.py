# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Innovatec API"
    
    # URL por defecto (útil para desarrollo local). 
    # Si existe en el archivo .env, Pydantic la sobrescribirá automáticamente.
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/evaluacion_cba"

    # Le indicamos a Pydantic que lea el archivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instanciamos los settings para importarlos en toda la app
settings = Settings()