from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional

from app.models.domain import AreaConocimiento, ProgramaFormacion
from app.schemas.academico import AreaConocimientoCreate, ProgramaFormacionCreate

# ==========================================
# CRUD ÁREA DE CONOCIMIENTO
# ==========================================
def get_area(db: Session, area_id: UUID) -> Optional[AreaConocimiento]:
    return db.get(AreaConocimiento, area_id)

def get_areas(db: Session, skip: int = 0, limit: int = 100) -> List[AreaConocimiento]:
    stmt = select(AreaConocimiento).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

def create_area(db: Session, obj_in: AreaConocimientoCreate) -> AreaConocimiento:
    db_area = AreaConocimiento(**obj_in.model_dump())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area


# ==========================================
# CRUD PROGRAMA DE FORMACIÓN
# ==========================================
def get_programa(db: Session, programa_id: UUID) -> Optional[ProgramaFormacion]:
    stmt = (
        select(ProgramaFormacion)
        .options(selectinload(ProgramaFormacion.area))
        .where(ProgramaFormacion.id == programa_id)
    )
    return db.scalars(stmt).first()

def get_programas(db: Session, skip: int = 0, limit: int = 100) -> List[ProgramaFormacion]:
    stmt = (
        select(ProgramaFormacion)
        .options(selectinload(ProgramaFormacion.area))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())

def create_programa(db: Session, obj_in: ProgramaFormacionCreate) -> ProgramaFormacion:
    db_programa = ProgramaFormacion(**obj_in.model_dump())
    db.add(db_programa)
    db.commit()
    db.refresh(db_programa)
    return db_programa