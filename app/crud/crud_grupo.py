from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional

from app.models.domain import GrupoProyecto, Aprendiz
from app.schemas.grupo import (
    GrupoProyectoCreate, 
    GrupoProyectoCreateConAprendices, 
    AprendizCreate
)

# ==========================================
# CRUD GRUPOS (PROYECTOS FORMATIVOS)
# ==========================================

def get_grupo(db: Session, grupo_id: UUID) -> Optional[GrupoProyecto]:
    """
    Obtiene un grupo por su ID. 
    Usa `selectinload` para precargar la lista de aprendices en una sola consulta SQL,
    evitando el problema de consultas N+1 y cumpliendo con el esquema Pydantic.
    """
    stmt = (
        select(GrupoProyecto)
        .options(selectinload(GrupoProyecto.aprendices))
        .where(GrupoProyecto.id == grupo_id)
    )
    return db.scalars(stmt).first()

def get_grupos(db: Session, skip: int = 0, limit: int = 100) -> List[GrupoProyecto]:
    """Obtiene un listado paginado de grupos con sus aprendices."""
    stmt = (
        select(GrupoProyecto)
        .options(selectinload(GrupoProyecto.aprendices))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())

def create_grupo_con_aprendices(
    db: Session, 
    obj_in: GrupoProyectoCreateConAprendices
) -> GrupoProyecto:
    """
    Crea el grupo y todos sus aprendices en una sola transacción de base de datos.
    Si un aprendiz falla (ej. documento duplicado), el grupo no se crea (Rollback automático).
    """
    # 1. Extraemos los datos del grupo excluyendo la lista de aprendices
    grupo_data = obj_in.model_dump(exclude={"aprendices"})
    db_grupo = GrupoProyecto(**grupo_data)
    
    # 2. Iteramos sobre los aprendices y los agregamos a la relación de SQLAlchemy
    for aprendiz_in in obj_in.aprendices:
        db_aprendiz = Aprendiz(**aprendiz_in.model_dump())
        db_grupo.aprendices.append(db_aprendiz)
    
    # 3. Guardamos todo en la base de datos
    db.add(db_grupo)
    db.commit()
    db.refresh(db_grupo)
    
    return db_grupo

def delete_grupo(db: Session, grupo_id: UUID) -> bool:
    """Elimina un grupo. Los aprendices se borrarán solos por el ON DELETE CASCADE."""
    db_grupo = get_grupo(db, grupo_id)
    if db_grupo:
        db.delete(db_grupo)
        db.commit()
        return True
    return False


# ==========================================
# CRUD APRENDICES (Individual)
# ==========================================

def get_aprendiz_by_documento(db: Session, documento: str) -> Optional[Aprendiz]:
    """Útil para validar que no se registre el mismo documento dos veces."""
    stmt = select(Aprendiz).where(Aprendiz.documento_identidad == documento)
    return db.scalars(stmt).first()

def add_aprendiz_to_grupo(db: Session, obj_in: AprendizCreate) -> Aprendiz:
    """Agrega un aprendiz individual a un grupo ya existente."""
    db_aprendiz = Aprendiz(**obj_in.model_dump())
    db.add(db_aprendiz)
    db.commit()
    db.refresh(db_aprendiz)
    return db_aprendiz