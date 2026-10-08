from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.schemas.plantilla import PlantillaEvaluacionCreate, PlantillaEvaluacionResponse
from app.crud import crud_plantilla, crud_academico
from app.api.dependencies import get_db

router = APIRouter(prefix="/plantillas", tags=["Plantillas de Evaluación (Rúbricas)"])

@router.post("/", response_model=PlantillaEvaluacionResponse, status_code=status.HTTP_201_CREATED)
def crear_plantilla_evaluacion(
    plantilla_in: PlantillaEvaluacionCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva plantilla/rúbrica de evaluación para un programa de formación.
    Valida que el programa exista y que la suma de ponderaciones sea 100%.
    """
    # 1. Verificar existencia del programa
    if not crud_academico.get_programa(db, programa_id=plantilla_in.programa_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El Programa de Formación con ID {plantilla_in.programa_id} no existe."
        )

    # 2. Validar que la suma de ponderaciones de los criterios dé 100%
    suma_pesos = sum(criterio.peso_porcentual for criterio in plantilla_in.criterios)
    if round(suma_pesos, 2) != 100.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La suma de las ponderaciones porcentuales debe ser exactamente 100%. Actual: {suma_pesos}%"
        )

    return crud_plantilla.create_plantilla(db=db, obj_in=plantilla_in)

@router.get("/programa/{programa_id}/activa", response_model=PlantillaEvaluacionResponse)
def obtener_plantilla_activa(programa_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene la rúbrica vigente/activa para un programa específico.
    """
    plantilla = crud_plantilla.get_plantilla_activa_por_programa(db=db, programa_id=programa_id)
    if not plantilla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay una plantilla activa registrada para este programa de formación."
        )
    return plantilla

@router.get("/programa/{programa_id}", response_model=List[PlantillaEvaluacionResponse])
def listar_plantillas_de_programa(programa_id: UUID, db: Session = Depends(get_db)):
    """
    Histórico de todas las plantillas (versiones anteriores y actuales) de un programa.
    """
    return crud_plantilla.get_plantillas_por_programa(db=db, programa_id=programa_id)