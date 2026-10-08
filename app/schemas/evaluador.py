from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.schemas.academico import AreaConocimientoResponse

# ==========================================
# EVALUADOR
# ==========================================
class EvaluadorBase(BaseModel):
    nombre_completo: str = Field(..., max_length=150)
    email: EmailStr

class EvaluadorCreate(EvaluadorBase):
    areas_ids: List[UUID] = Field(..., min_length=1, description="Lista de IDs de áreas que puede evaluar")

class EvaluadorResponse(EvaluadorBase):
    id: UUID
    auth_user_id: Optional[UUID] = None
    creado_en: datetime
    areas: List[AreaConocimientoResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ASIGNACIÓN DE EVALUACIÓN
# ==========================================
class AsignacionEvaluacionCreate(BaseModel):
    evaluador_id: UUID
    grupo_id: UUID

class AsignacionEvaluacionResponse(BaseModel):
    id: UUID
    evaluador_id: UUID
    grupo_id: UUID
    estado: str
    fecha_asignacion: datetime

    model_config = ConfigDict(from_attributes=True)