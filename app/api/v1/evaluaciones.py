from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel
from typing import List

from app.api.dependencies import get_db
from app.models.domain import AsignacionEvaluacion, GrupoProyecto, PlantillaEvaluacion, RegistroEvaluacion, ProgramaFormacion, AreaConocimiento

router = APIRouter(prefix="/evaluaciones", tags=["Proceso de Evaluación Digital"])

# ==========================================
# ESQUEMAS PYDANTIC LOCALES
# ==========================================
class RespuestaCriterio(BaseModel):
    criterio_indice: int
    calificacion: int  # Ej. del 1 al 5

class EnviarEvaluacionDigital(BaseModel):
    grupo_id: UUID
    evaluador_id: UUID
    respuestas: List[RespuestaCriterio]

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/desbloquear-formulario")
def desbloquear_formulario(grupo_id: UUID, evaluador_id: UUID, db: Session = Depends(get_db)):
    """
    Se llama cuando el instructor escanea el QR del stand.
    Verifica si tiene asignado este proyecto y devuelve la rúbrica estructurada.
    """
    stmt_asig = (
        select(AsignacionEvaluacion)
        .options(selectinload(AsignacionEvaluacion.grupo))
        .where(
            AsignacionEvaluacion.grupo_id == grupo_id,
            AsignacionEvaluacion.evaluador_id == evaluador_id
        )
    )
    asignacion = db.scalars(stmt_asig).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes autorización para evaluar a este grupo o el código QR es inválido."
        )
        
    # Extraer la rúbrica activa directamente mediante el programa_id del grupo
    stmt_plantilla = select(PlantillaEvaluacion).where(
        PlantillaEvaluacion.programa_id == asignacion.grupo.programa_id,
        PlantillaEvaluacion.activa == True
    )
    plantilla = db.scalars(stmt_plantilla).first()
    
    if not plantilla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="El programa de formación no tiene una plantilla de evaluación activa."
        )
    
    return {
        "asignacion_id": asignacion.id,
        "estado": asignacion.estado,
        "proyecto": asignacion.grupo.nombre_proyecto,
        "criterios": plantilla.criterios # El JSON que Flutter renderizará dinámicamente
    }

@router.post("/guardar-digital", status_code=status.HTTP_201_CREATED)
def guardar_evaluacion_digital(payload: EnviarEvaluacionDigital, db: Session = Depends(get_db)):
    """
    Recibe el formulario lleno desde la app de Flutter, calcula la nota y guarda.
    """
    # 1. Obtener la asignación y cargar el grupo
    stmt_asig = (
        select(AsignacionEvaluacion)
        .options(selectinload(AsignacionEvaluacion.grupo))
        .where(
            AsignacionEvaluacion.grupo_id == payload.grupo_id,
            AsignacionEvaluacion.evaluador_id == payload.evaluador_id
        )
    )
    asignacion = db.scalars(stmt_asig).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada.")

    # 2. Obtener la plantilla activa para extraer los pesos porcentuales
    stmt_plantilla = select(PlantillaEvaluacion).where(
        PlantillaEvaluacion.programa_id == asignacion.grupo.programa_id,
        PlantillaEvaluacion.activa == True
    )
    plantilla = db.scalars(stmt_plantilla).first()
    criterios_bd = plantilla.criterios
    
    # 3. Calcular nota ponderada
    puntaje_final = 0.0
    for respuesta in payload.respuestas:
        # Extraemos el peso desde el JSON de la BD (ej. 40.0) y lo dividimos en 100 (0.40)
        peso_porcentual = float(criterios_bd[respuesta.criterio_indice].get("peso_porcentual", 0)) / 100.0
        puntaje_final += (respuesta.calificacion * peso_porcentual)
        
    puntaje_final = round(puntaje_final, 1)

    # 4. Guardar o actualizar registro
    stmt_registro = select(RegistroEvaluacion).where(RegistroEvaluacion.asignacion_id == asignacion.id)
    registro_existente = db.scalars(stmt_registro).first()
    
    resultados_json = [r.model_dump() for r in payload.respuestas]

    if registro_existente:
        registro_existente.resultados_crudos = resultados_json
        registro_existente.puntaje_final = puntaje_final
        mensaje = "Evaluación actualizada exitosamente"
    else:
        nuevo_registro = RegistroEvaluacion(
            asignacion_id=asignacion.id,
            resultados_crudos=resultados_json,
            puntaje_final=puntaje_final
        )
        db.add(nuevo_registro)
        mensaje = "Evaluación guardada exitosamente"

    # Marcar el turno como evaluado
    asignacion.estado = "PROCESADA"
    db.commit()

    return {
        "mensaje": mensaje, 
        "puntaje_final": puntaje_final,
        "asignacion_id": asignacion.id
    }

@router.get("/ranking")
def obtener_ranking_proyectos(db: Session = Depends(get_db)):
    """
    Devuelve el ranking de proyectos evaluados, agrupados por área de conocimiento
    y ordenados por puntaje final de mayor a menor.
    """
    stmt = (
        select(
            AreaConocimiento.nombre.label("area_nombre"),
            GrupoProyecto.id,
            GrupoProyecto.nombre_proyecto,
            GrupoProyecto.trimestre,
            RegistroEvaluacion.puntaje_final
        )
        .join(ProgramaFormacion, GrupoProyecto.programa_id == ProgramaFormacion.id)
        .join(AreaConocimiento, ProgramaFormacion.area_id == AreaConocimiento.id)
        .join(AsignacionEvaluacion, AsignacionEvaluacion.grupo_id == GrupoProyecto.id)
        .join(RegistroEvaluacion, RegistroEvaluacion.asignacion_id == AsignacionEvaluacion.id)
        .where(RegistroEvaluacion.puntaje_final.is_not(None))
        .order_by(AreaConocimiento.nombre, RegistroEvaluacion.puntaje_final.desc())
    )
    
    filas = db.execute(stmt).all()
    
    ranking_dict = {}
    for fila in filas:
        area = fila.area_nombre
        if area not in ranking_dict:
            ranking_dict[area] = []
            
        ranking_dict[area].append({
            "id": str(fila.id),
            "nombre_proyecto": fila.nombre_proyecto,
            "trimestre": fila.trimestre,
            "puntaje_final": float(fila.puntaje_final)
        })
        
    # Convertir el diccionario en una lista amigable para Flutter
    resultado = [
        {"area": k, "proyectos": v} 
        for k, v in ranking_dict.items()
    ]
    
    return resultado