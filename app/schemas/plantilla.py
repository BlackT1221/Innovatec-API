from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# ==========================================
# ESTRUCTURA DEL CRITERIO DENTRO DEL JSONB
# ==========================================
class CriterioItem(BaseModel):
    id: str = Field(..., description="Identificador único del criterio (ej. c1, c2)")
    titulo: str = Field(..., max_length=150, description="Ej. Arquitectura de BD o Calidad de Costura")
    descripcion: Optional[str] = Field(None, description="Detalle de lo que el evaluador debe observar")
    peso_porcentual: float = Field(..., ge=0, le=100, description="Ponderación del criterio (0 a 100%)")
    escala_maxima: int = Field(5, description="Valor máximo de la escala (ej. 5 para escala 1 a 5)")

class RubricaPayload(BaseModel):
    criterios: List[CriterioItem] = Field(..., min_length=1)

# ==========================================
# PLANTILLA DE EVALUACIÓN
# ==========================================
class PlantillaEvaluacionBase(BaseModel):
    version: str = Field("1.0", max_length=20)
    activa: bool = True

class PlantillaEvaluacionCreate(PlantillaEvaluacionBase):
    programa_id: UUID
    criterios: List[CriterioItem] = Field(..., min_length=1, description="Lista de criterios de evaluación")

class PlantillaEvaluacionResponse(PlantillaEvaluacionBase):
    id: UUID
    programa_id: UUID
    criterios: List[CriterioItem]
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)