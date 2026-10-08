from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================
# ESQUEMAS DE APRENDIZ
# ==========================================
class AprendizBase(BaseModel):
    documento_identidad: str = Field(..., max_length=50, description="Cédula, TI o PEP del aprendiz")
    nombre_completo: str = Field(..., max_length=150)

class AprendizCreate(AprendizBase):
    grupo_id: UUID

class AprendizResponse(AprendizBase):
    id: UUID
    grupo_id: UUID
    creado_en: datetime

    # Permite que Pydantic lea los datos directamente del objeto SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ESQUEMAS DE GRUPO (PROYECTO)
# ==========================================
class GrupoProyectoBase(BaseModel):
    nombre_proyecto: str = Field(..., max_length=200)
    logo_url: Optional[str] = Field(None, max_length=255)
    trimestre: str = Field(..., max_length=20, examples=["2026-3", "2026-4"])

class GrupoProyectoCreate(GrupoProyectoBase):
    programa_id: UUID

class GrupoProyectoResponse(GrupoProyectoBase):
    id: UUID
    programa_id: UUID
    creado_en: datetime
    # Anidamos los aprendices para que al consultar un grupo, traiga a sus integrantes
    aprendices: List[AprendizResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ESQUEMA AVANZADO (Creación Anidada)
# ==========================================
class AprendizCreateSinGrupo(AprendizBase):
    """Usado cuando creas el grupo y los aprendices al mismo tiempo"""
    pass

class GrupoProyectoCreateConAprendices(GrupoProyectoCreate):
    """
    Permite enviar un JSON con los datos del grupo y una lista de sus
    aprendices en una sola petición al backend.
    """
    aprendices: List[AprendizCreateSinGrupo] = Field(..., min_length=1)