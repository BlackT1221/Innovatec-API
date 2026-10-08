from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional

from app.models.domain import Evaluador, AreaConocimiento, AsignacionEvaluacion, GrupoProyecto
from app.schemas.evaluador import EvaluadorCreate, AsignacionEvaluacionCreate

# ==========================================
# CRUD EVALUADORES
# ==========================================
def get_evaluador(db: Session, evaluador_id: UUID) -> Optional[Evaluador]:
    stmt = (
        select(Evaluador)
        .options(selectinload(Evaluador.areas))
        .where(Evaluador.id == evaluador_id)
    )
    return db.scalars(stmt).first()

def get_evaluadores(db: Session, skip: int = 0, limit: int = 100) -> List[Evaluador]:
    stmt = (
        select(Evaluador)
        .options(selectinload(Evaluador.areas))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())

def create_evaluador(db: Session, obj_in: EvaluadorCreate) -> Evaluador:
    db_evaluador = Evaluador(
        nombre_completo=obj_in.nombre_completo,
        email=obj_in.email
    )
    
    # Asociar las áreas de conocimiento autorizadas
    stmt_areas = select(AreaConocimiento).where(AreaConocimiento.id.in_(obj_in.areas_ids))
    areas = db.scalars(stmt_areas).all()
    db_evaluador.areas.extend(areas)
    
    db.add(db_evaluador)
    db.commit()
    db.refresh(db_evaluador)
    return db_evaluador


# ==========================================
# CRUD ASIGNACIONES CON VALIDACIÓN DE ÁREA
# ==========================================
def validar_compatibilidad_evaluador(db: Session, evaluador_id: UUID, grupo_id: UUID) -> bool:
    """
    Verifica que el grupo pertenezca a un programa cuya área de conocimiento
    esté autorizada para el evaluador.
    """
    evaluador = get_evaluador(db, evaluador_id)
    if not evaluador:
        return False
        
    stmt_grupo = (
        select(GrupoProyecto)
        .options(selectinload(GrupoProyecto.programa))
        .where(GrupoProyecto.id == grupo_id)
    )
    grupo = db.scalars(stmt_grupo).first()
    if not grupo or not grupo.programa:
        return False

    areas_evaluador_ids = [area.id for area in evaluador.areas]
    return grupo.programa.area_id in areas_evaluador_ids

def create_asignacion(db: Session, obj_in: AsignacionEvaluacionCreate) -> AsignacionEvaluacion:
    db_asignacion = AsignacionEvaluacion(**obj_in.model_dump())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def get_asignaciones(db: Session, skip: int = 0, limit: int = 100) -> List[AsignacionEvaluacion]:
    stmt = select(AsignacionEvaluacion).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

def get_asignaciones_por_evaluador(db: Session, evaluador_id: UUID) -> List[AsignacionEvaluacion]:
    """Obtiene todas las asignaciones de proyectos para un evaluador específico."""
    stmt = (
        select(AsignacionEvaluacion)
        .options(
            selectinload(AsignacionEvaluacion.grupo),
            selectinload(AsignacionEvaluacion.registro_fisico)
        )
        .where(AsignacionEvaluacion.evaluador_id == evaluador_id)
    )
    return list(db.scalars(stmt).all())