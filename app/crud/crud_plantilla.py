from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.domain import PlantillaEvaluacion, ProgramaFormacion
from app.schemas.plantilla import PlantillaEvaluacionCreate

def get_plantilla(db: Session, plantilla_id: UUID) -> Optional[PlantillaEvaluacion]:
    return db.get(PlantillaEvaluacion, plantilla_id)

def get_plantilla_activa_por_programa(db: Session, programa_id: UUID) -> Optional[PlantillaEvaluacion]:
    """Obtiene la plantilla actualmente activa para un programa de formación."""
    stmt = (
        select(PlantillaEvaluacion)
        .where(
            PlantillaEvaluacion.programa_id == programa_id,
            PlantillaEvaluacion.activa == True
        )
    )
    return db.scalars(stmt).first()

def create_plantilla(db: Session, obj_in: PlantillaEvaluacionCreate) -> PlantillaEvaluacion:
    # 1. Convertir la lista de CriterioItem a una lista de diccionarios para el campo JSONB
    criterios_json = [criterio.model_dump() for criterio in obj_in.criterios]

    # 2. Si se marca como activa, desactivar cualquier otra plantilla previa del mismo programa
    if obj_in.activa:
        stmt_desactivar = (
            select(PlantillaEvaluacion)
            .where(
                PlantillaEvaluacion.programa_id == obj_in.programa_id,
                PlantillaEvaluacion.activa == True
            )
        )
        plantillas_activas = db.scalars(stmt_desactivar).all()
        for p in plantillas_activas:
            p.activa = False

    # 3. Crear la nueva plantilla
    db_plantilla = PlantillaEvaluacion(
        programa_id=obj_in.programa_id,
        version=obj_in.version,
        criterios=criterios_json,
        activa=obj_in.activa
    )
    
    db.add(db_plantilla)
    db.commit()
    db.refresh(db_plantilla)
    return db_plantilla

def get_plantillas_por_programa(db: Session, programa_id: UUID) -> List[PlantillaEvaluacion]:
    stmt = select(PlantillaEvaluacion).where(PlantillaEvaluacion.programa_id == programa_id)
    return list(db.scalars(stmt).all())