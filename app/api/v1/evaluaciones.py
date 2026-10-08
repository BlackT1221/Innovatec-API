from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.dependencies import get_db
from app.crud.crud_evaluador import get_asignaciones # Deberás crear un get_asignacion individual
from app.models.domain import AsignacionEvaluacion, GrupoProyecto, Evaluador, PlantillaEvaluacion
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.pdf_generator import generar_hoja_evaluacion_pdf

from app.services.omr_processor import alinear_hoja_y_leer_qr, procesar_burbujas
from app.models.domain import RegistroEvaluacionFisica


router = APIRouter(prefix="/evaluaciones", tags=["Proceso Físico OMR"])

@router.get("/{asignacion_id}/imprimir", response_class=StreamingResponse)
def imprimir_hoja_omr(asignacion_id: UUID, db: Session = Depends(get_db)):
    """
    Genera y descarga el PDF de evaluación con marcadores y código QR.
    """
    # 1. Buscar la asignación con relaciones necesarias
    stmt = (
        select(AsignacionEvaluacion)
        .options(
            selectinload(AsignacionEvaluacion.evaluador),
            selectinload(AsignacionEvaluacion.grupo).selectinload(GrupoProyecto.programa)
        )
        .where(AsignacionEvaluacion.id == asignacion_id)
    )
    asignacion = db.scalars(stmt).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
        
    # 2. Obtener la plantilla activa de ese programa
    stmt_plantilla = (
        select(PlantillaEvaluacion)
        .where(
            PlantillaEvaluacion.programa_id == asignacion.grupo.programa_id,
            PlantillaEvaluacion.activa == True
        )
    )
    plantilla = db.scalars(stmt_plantilla).first()
    
    if not plantilla:
        raise HTTPException(status_code=400, detail="El programa no tiene una plantilla de evaluación activa.")
        
    # 3. Generar el PDF en memoria
    pdf_buffer = generar_hoja_evaluacion_pdf(
        asignacion_id=str(asignacion.id),
        nombre_evaluador=asignacion.evaluador.nombre_completo,
        nombre_proyecto=asignacion.grupo.nombre_proyecto,
        criterios=plantilla.criterios
    )
    
    # 4. Retornar el PDF al navegador
    headers = {
        'Content-Disposition': f'inline; filename="evaluacion_{asignacion.grupo.nombre_proyecto}.pdf"'
    }
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

@router.post("/escanear", status_code=status.HTTP_201_CREATED)
async def escanear_hoja_omr(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    image_bytes = await file.read()
    
    # 1. OpenCV Paso A: Alinear y extraer solo el QR
    try:
        warped_img, asignacion_id_str = alinear_hoja_y_leer_qr(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # 2. Consultar la BD para obtener la asignación y la plantilla real
    stmt_asignacion = (
        select(AsignacionEvaluacion)
        .options(selectinload(AsignacionEvaluacion.grupo).selectinload(GrupoProyecto.programa))
        .where(AsignacionEvaluacion.id == asignacion_id_str)
    )
    asignacion = db.scalars(stmt_asignacion).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="El QR pertenece a una asignación que no existe.")
        
    stmt_plantilla = select(PlantillaEvaluacion).where(
        PlantillaEvaluacion.programa_id == asignacion.grupo.programa_id,
        PlantillaEvaluacion.activa == True
    )
    plantilla = db.scalars(stmt_plantilla).first()
    
    if not plantilla:
        raise HTTPException(status_code=404, detail="El programa no tiene una plantilla activa.")
    
    criterios_bd = plantilla.criterios
    num_criterios_reales = len(criterios_bd)
    
    # 3. OpenCV Paso B: Leer burbujas
    resultados_crudos = procesar_burbujas(warped_img, num_criterios_reales)
    
    # 4. Calcular el Puntaje Ponderado
    puntaje_final = 0.0
    for idx, resultado in enumerate(resultados_crudos):
        calificacion = resultado["calificacion"] 
        peso_porcentual = float(criterios_bd[idx].get("peso_porcentual", 0)) / 100.0
        
        if calificacion > 0:
            puntaje_final += (calificacion * peso_porcentual)
            
    puntaje_final = round(puntaje_final, 1)

    # 5. GUARDAR O ACTUALIZAR EN BASE DE DATOS
    stmt_registro_existente = select(RegistroEvaluacionFisica).where(
        RegistroEvaluacionFisica.asignacion_id == asignacion.id
    )
    registro_existente = db.scalars(stmt_registro_existente).first()

    if registro_existente:
        # Si ya existe, actualizamos los datos (útil si el instructor escanea de nuevo para corregir)
        registro_existente.resultados_crudos = resultados_crudos
        registro_existente.puntaje_final = puntaje_final
        db.commit()
        mensaje = "Evaluación re-escaneada y nota actualizada exitosamente"
    else:
        # Si no existe, creamos uno nuevo
        registro_nuevo = RegistroEvaluacionFisica(
            asignacion_id=asignacion.id,
            imagen_escaneada_url="pendiente_subir_a_supabase.jpg",
            resultados_crudos=resultados_crudos,
            puntaje_final=puntaje_final
        )
        asignacion.estado = "PROCESADA"
        db.add(registro_nuevo)
        db.commit()
        mensaje = "Evaluación dinámica procesada exitosamente"
    
    return {
        "mensaje": mensaje,
        "asignacion_id": asignacion.id,
        "puntaje_final": puntaje_final,
        "detalle": resultados_crudos
    }