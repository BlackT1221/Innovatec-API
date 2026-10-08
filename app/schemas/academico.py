from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ==========================================
# ÁREA DE CONOCIMIENTO
# ==========================================
class AreaConocimientoBase(BaseModel):
    nombre: str = Field(..., max_length=100, examples=["Sistemas y Desarrollo", "Confección y Diseño"])

class AreaConocimientoCreate(AreaConocimientoBase):
    pass

class AreaConocimientoResponse(AreaConocimientoBase):
    id: UUID
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PROGRAMA DE FORMACIÓN
# ==========================================
class ProgramaFormacionBase(BaseModel):
    nombre: str = Field(..., max_length=150, examples=["ADSO", "Desarrollo de Software", "Confección Industrial"])

class ProgramaFormacionCreate(ProgramaFormacionBase):
    area_id: UUID

class ProgramaFormacionResponse(ProgramaFormacionBase):
    id: UUID
    area_id: UUID
    creado_en: datetime
    area: Optional[AreaConocimientoResponse] = None

    model_config = ConfigDict(from_attributes=True)