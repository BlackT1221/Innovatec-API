from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.models.domain import PlantillaEvaluacion
from app.schemas.plantilla import PlantillaEvaluacionCreate, PlantillaEvaluacionResponse
from app.crud import crud_plantilla, crud_academico
from app.api.dependencies import get_db

import csv
import io
from collections import defaultdict
from fastapi import UploadFile, File

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

@router.post("/cargar-csv", status_code=status.HTTP_201_CREATED)
async def cargar_plantillas_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Carga masivamente rúbricas/plantillas de evaluación desde un archivo CSV.
    Agrupa los criterios por programa_id y valida que la suma de ponderaciones sea 100%.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe tener extensión .csv")

    contents = await file.read()
    buffer = io.StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(buffer)

    plantillas_dict = defaultdict(list)
    errores = []

    # 1. Parsear y agrupar criterios por programa_id
    for fila_num, row in enumerate(reader, start=2):
        prog_id = row.get("programa_id", "").strip()
        crit_id = row.get("criterio_id", "").strip()
        titulo = row.get("titulo", "").strip()
        descripcion = row.get("descripcion", "").strip()
        peso_str = row.get("peso_porcentual", "").strip()

        if not prog_id or not crit_id or not titulo or not peso_str:
            errores.append(f"Fila {fila_num}: Datos incompletos.")
            continue

        try:
            peso = float(peso_str)
        except ValueError:
            errores.append(f"Fila {fila_num}: Ponderación '{peso_str}' no es un número válido.")
            continue

        plantillas_dict[prog_id].append({
            "id": crit_id,
            "titulo": titulo,
            "descripcion": descripcion,
            "peso_porcentual": peso,
            "escala_maxima": 5
        })

    plantillas_creadas = 0

    # 2. Procesar cada programa y guardar la plantilla
    for prog_id_str, criterios in plantillas_dict.items():
        try:
            prog_uuid = UUID(prog_id_str)
        except ValueError:
            errores.append(f"Programa ID {prog_id_str} inválido.")
            continue

        if not crud_academico.get_programa(db, programa_id=prog_uuid):
            errores.append(f"Programa con ID {prog_id_str} no existe en la BD.")
            continue

        # Validar que la suma de los criterios de ese programa dé 100%
        suma_pesos = sum(c["peso_porcentual"] for c in criterios)
        if round(suma_pesos, 2) != 100.0:
            errores.append(f"Programa {prog_id_str}: La suma de pesos es {suma_pesos}%, debe ser exactamente 100%.")
            continue

        # Desactivar plantillas previas para este programa
        stmt_desactivar = select(PlantillaEvaluacion).where(
            PlantillaEvaluacion.programa_id == prog_uuid,
            PlantillaEvaluacion.activa == True
        )
        for p in db.scalars(stmt_desactivar).all():
            p.activa = False

        # Crear la nueva plantilla activa
        nueva_plantilla = PlantillaEvaluacion(
            programa_id=prog_uuid,
            version="1.0",
            criterios=criterios,
            activa=True
        )
        db.add(nueva_plantilla)
        plantillas_creadas += 1

    db.commit()

    return {
        "mensaje": f"Proceso finalizado. Plantillas creadas: {plantillas_creadas}",
        "plantillas_creadas": plantillas_creadas,
        "errores": errores
    }