from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.schemas.evaluador import (
    EvaluadorCreate,
    EvaluadorResponse,
    AsignacionEvaluacionCreate,
    AsignacionEvaluacionResponse
)
from app.crud import crud_evaluador
from app.api.dependencies import get_db

router = APIRouter(prefix="/evaluadores", tags=["Evaluadores y Asignaciones"])

@router.post("/", response_model=EvaluadorResponse, status_code=status.HTTP_201_CREATED)
def crear_evaluador(evaluador_in: EvaluadorCreate, db: Session = Depends(get_db)):
    return crud_evaluador.create_evaluador(db=db, obj_in=evaluador_in)

@router.get("/", response_model=List[EvaluadorResponse])
def listar_evaluadores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_evaluador.get_evaluadores(db=db, skip=skip, limit=limit)

@router.post("/asignar/", response_model=AsignacionEvaluacionResponse, status_code=status.HTTP_201_CREATED)
def asignar_proyecto_a_evaluador(
    asignacion_in: AsignacionEvaluacionCreate,
    db: Session = Depends(get_db)
):
    """
    Asigna un grupo formativo a un evaluador.
    Valida automáticamente que la rama del evaluador coincida con el área del proyecto.
    """
    es_valido = crud_evaluador.validar_compatibilidad_evaluador(
        db, 
        evaluador_id=asignacion_in.evaluador_id, 
        grupo_id=asignacion_in.grupo_id
    )
    
    if not es_valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incompatibilidad de perfil: El evaluador no tiene autorizada el área de conocimiento a la que pertenece este proyecto."
        )
        
    return crud_evaluador.create_asignacion(db=db, obj_in=asignacion_in)

@router.get("/asignaciones/", response_model=List[AsignacionEvaluacionResponse])
def listar_asignaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_evaluador.get_asignaciones(db=db, skip=skip, limit=limit)