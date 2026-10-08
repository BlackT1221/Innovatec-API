from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.schemas.grupo import (
    GrupoProyectoResponse, 
    GrupoProyectoCreateConAprendices,
    AprendizCreate,
    AprendizResponse
)
from app.crud import crud_grupo
# Asumimos que tienes una dependencia get_db configurada para inyectar la sesión
from app.api.dependencies import get_db 

router = APIRouter(prefix="/grupos", tags=["Proyectos Formativos"])

# ==========================================
# ENDPOINTS DE GRUPOS
# ==========================================

@router.post("/", response_model=GrupoProyectoResponse, status_code=status.HTTP_201_CREATED)
def crear_grupo_con_aprendices(
    grupo_in: GrupoProyectoCreateConAprendices,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo proyecto formativo del CBA e inscribe automáticamente 
    a todos los aprendices asociados en la misma petición.
    """
    # Validación: Verificar que los documentos de los aprendices no existan ya
    for aprendiz in grupo_in.aprendices:
        if crud_grupo.get_aprendiz_by_documento(db, documento=aprendiz.documento_identidad):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El aprendiz con documento {aprendiz.documento_identidad} ya está registrado en el sistema."
            )
            
    return crud_grupo.create_grupo_con_aprendices(db=db, obj_in=grupo_in)

@router.get("/", response_model=List[GrupoProyectoResponse])
def listar_grupos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Devuelve la lista paginada de todos los grupos y sus aprendices.
    """
    return crud_grupo.get_grupos(db=db, skip=skip, limit=limit)

@router.get("/{grupo_id}", response_model=GrupoProyectoResponse)
def obtener_grupo(grupo_id: UUID, db: Session = Depends(get_db)):
    """
    Busca un proyecto formativo específico por su ID.
    """
    grupo = crud_grupo.get_grupo(db=db, grupo_id=grupo_id)
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return grupo

@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_grupo(grupo_id: UUID, db: Session = Depends(get_db)):
    """
    Elimina un grupo. Por cascada, eliminará a los aprendices asociados.
    """
    eliminado = crud_grupo.delete_grupo(db=db, grupo_id=grupo_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return None

# ==========================================
# ENDPOINTS DE APRENDICES (Operaciones extra)
# ==========================================

@router.post("/aprendices/", response_model=AprendizResponse, status_code=status.HTTP_201_CREATED, tags=["Aprendices"])
def agregar_aprendiz_a_grupo(
    aprendiz_in: AprendizCreate,
    db: Session = Depends(get_db)
):
    """
    Agrega un aprendiz a un grupo ya existente.
    """
    if crud_grupo.get_aprendiz_by_documento(db, documento=aprendiz_in.documento_identidad):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El documento ya se encuentra registrado."
        )
        
    # Validar que el grupo exista antes de insertar
    if not crud_grupo.get_grupo(db, grupo_id=aprendiz_in.grupo_id):
        raise HTTPException(status_code=404, detail="El grupo asignado no existe.")
        
    return crud_grupo.add_aprendiz_to_grupo(db=db, obj_in=aprendiz_in)