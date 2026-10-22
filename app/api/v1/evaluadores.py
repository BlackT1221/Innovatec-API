from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from typing import List
from uuid import UUID
from app.models.domain import Evaluador, GrupoProyecto, ProgramaFormacion, AsignacionEvaluacion
from sqlalchemy import select


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

@router.get("/evaluador/{evaluador_id}/asignaciones")
def listar_asignaciones_de_evaluador(evaluador_id: UUID, db: Session = Depends(get_db)):
    """Retorna la lista de proyectos asignados a un instructor con su estado actual."""
    asignaciones = crud_evaluador.get_asignaciones_por_evaluador(db, evaluador_id=evaluador_id)
    
    resultado = []
    for asig in asignaciones:
        resultado.append({
            "asignacion_id": str(asig.id),
            "estado": asig.estado,
            "proyecto": {
                "id": str(asig.grupo.id),
                "nombre_proyecto": asig.grupo.nombre_proyecto,
                "trimestre": asig.grupo.trimestre,
                "logo_url": asig.grupo.logo_url
            },
            "puntaje_final": float(asig.registro_evaluacion.puntaje_final) if asig.registro_evaluacion else None
        })
    return resultado

@router.delete("/asignar/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    """Elimina una asignación existente."""
    stmt = select(AsignacionEvaluacion).where(AsignacionEvaluacion.id == asignacion_id)
    asignacion = db.scalars(stmt).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="La asignación no existe.")
        
    db.delete(asignacion)
    db.commit()
    return None

@router.get("/{evaluador_id}/grupos-compatibles")
def listar_grupos_compatibles(evaluador_id: UUID, db: Session = Depends(get_db)):
    """
    Devuelve los grupos de proyectos que pertenecen a alguna de las áreas 
    del evaluador, excluyendo absolutamente todos los que YA tienen una asignación previa.
    """
    # 1. Obtener las áreas del evaluador
    stmt_eval = select(Evaluador).options(selectinload(Evaluador.areas)).where(Evaluador.id == evaluador_id)
    evaluador = db.scalars(stmt_eval).first()
    
    if not evaluador:
        raise HTTPException(status_code=404, detail="Evaluador no encontrado")
        
    areas_ids = [area.id for area in evaluador.areas]
    if not areas_ids:
        return [] # No tiene áreas de conocimiento, no puede evaluar nada.
        
    # 2. AQUÍ ESTÁ EL CAMBIO: Obtener IDs de TODOS los grupos que ya tienen una asignación (sin importar el instructor)
    stmt_asignados = select(AsignacionEvaluacion.grupo_id)
    grupos_asignados_ids = db.scalars(stmt_asignados).all()
    
    # 3. Buscar grupos cuyo programa pertenezca a sus áreas, descartando los que ya están asignados a alguien
    stmt_grupos = select(GrupoProyecto).join(ProgramaFormacion).where(ProgramaFormacion.area_id.in_(areas_ids))
    
    if grupos_asignados_ids:
        stmt_grupos = stmt_grupos.where(~GrupoProyecto.id.in_(grupos_asignados_ids))
        
    grupos_compatibles = db.scalars(stmt_grupos).all()
    
    return [
        {
            "id": str(g.id),
            "nombre_proyecto": g.nombre_proyecto,
            "trimestre": g.trimestre
        } for g in grupos_compatibles
    ]