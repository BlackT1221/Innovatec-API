from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.schemas.academico import (
    AreaConocimientoCreate,
    AreaConocimientoResponse,
    ProgramaFormacionCreate,
    ProgramaFormacionResponse
)
from app.crud import crud_academico
from app.api.dependencies import get_db

router = APIRouter(prefix="/academico", tags=["Estructura Académica"])

# ==========================================
# ENDPOINTS ÁREAS DE CONOCIMIENTO
# ==========================================
@router.post("/areas/", response_model=AreaConocimientoResponse, status_code=status.HTTP_201_CREATED)
def crear_area(area_in: AreaConocimientoCreate, db: Session = Depends(get_db)):
    return crud_academico.create_area(db=db, obj_in=area_in)

@router.get("/areas/", response_model=List[AreaConocimientoResponse])
def listar_areas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_academico.get_areas(db=db, skip=skip, limit=limit)


# ==========================================
# ENDPOINTS PROGRAMAS DE FORMACIÓN
# ==========================================
@router.post("/programas/", response_model=ProgramaFormacionResponse, status_code=status.HTTP_201_CREATED)
def crear_programa(programa_in: ProgramaFormacionCreate, db: Session = Depends(get_db)):
    # Validar que el área asignada exista
    if not crud_academico.get_area(db, area_id=programa_in.area_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El Área de Conocimiento con ID {programa_in.area_id} no existe."
        )
    return crud_academico.create_programa(db=db, obj_in=programa_in)

@router.get("/programas/", response_model=List[ProgramaFormacionResponse])
def listar_programas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_academico.get_programas(db=db, skip=skip, limit=limit)