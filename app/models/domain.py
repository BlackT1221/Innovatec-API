import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, Boolean, Numeric, DateTime, Table, UniqueConstraint, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

# Clase base para todos los modelos
class Base(DeclarativeBase):
    pass

# ==========================================
# 1. TABLA PIVOTE (Many-to-Many)
# ==========================================
evaluador_area = Table(
    "evaluador_area",
    Base.metadata,
    Column("evaluador_id", UUID(as_uuid=True), ForeignKey("evaluador.id", ondelete="CASCADE"), primary_key=True),
    Column("area_id", UUID(as_uuid=True), ForeignKey("area_conocimiento.id", ondelete="CASCADE"), primary_key=True)
)

# ==========================================
# 2. NÚCLEO DE PERFILES Y ÁREAS
# ==========================================
class AreaConocimiento(Base):
    __tablename__ = "area_conocimiento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    evaluadores: Mapped[List["Evaluador"]] = relationship(secondary=evaluador_area, back_populates="areas")
    programas: Mapped[List["ProgramaFormacion"]] = relationship(back_populates="area")

class Evaluador(Base):
    __tablename__ = "evaluador"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    auth_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), unique=True, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    areas: Mapped[List["AreaConocimiento"]] = relationship(secondary=evaluador_area, back_populates="evaluadores")
    asignaciones: Mapped[List["AsignacionEvaluacion"]] = relationship(back_populates="evaluador")

# ==========================================
# 3. FORMACIÓN Y RÚBRICAS
# ==========================================
class ProgramaFormacion(Base):
    __tablename__ = "programa_formacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    area_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("area_conocimiento.id", ondelete="RESTRICT"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    area: Mapped["AreaConocimiento"] = relationship(back_populates="programas")
    plantillas: Mapped[List["PlantillaEvaluacion"]] = relationship(back_populates="programa")
    grupos: Mapped[List["GrupoProyecto"]] = relationship(back_populates="programa")

class PlantillaEvaluacion(Base):
    __tablename__ = "plantilla_evaluacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    programa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programa_formacion.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    criterios = mapped_column(JSONB, nullable=False) # JSONB nativo
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    programa: Mapped["ProgramaFormacion"] = relationship(back_populates="plantillas")

# ==========================================
# 4. GRUPOS Y PROYECTOS
# ==========================================
class GrupoProyecto(Base):
    __tablename__ = "grupo_proyecto"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_proyecto: Mapped[str] = mapped_column(String(200), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    programa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programa_formacion.id", ondelete="RESTRICT"))
    trimestre: Mapped[str] = mapped_column(String(20), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    programa: Mapped["ProgramaFormacion"] = relationship(back_populates="grupos")
    aprendices: Mapped[List["Aprendiz"]] = relationship(back_populates="grupo", cascade="all, delete-orphan")
    asignaciones: Mapped[List["AsignacionEvaluacion"]] = relationship(back_populates="grupo")

class Aprendiz(Base):
    __tablename__ = "aprendiz"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_identidad: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    grupo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grupo_proyecto.id", ondelete="CASCADE"), index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    grupo: Mapped["GrupoProyecto"] = relationship(back_populates="aprendices")

# ==========================================
# 5. FLUJO OMR / EVALUACIONES
# ==========================================
class AsignacionEvaluacion(Base):
    __tablename__ = "asignacion_evaluacion"
    __table_args__ = (UniqueConstraint("evaluador_id", "grupo_id", name="uix_evaluador_grupo"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluador.id", ondelete="CASCADE"))
    grupo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grupo_proyecto.id", ondelete="CASCADE"))
    estado: Mapped[str] = mapped_column(String(50), default="PENDIENTE", index=True)
    fecha_asignacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    evaluador: Mapped["Evaluador"] = relationship(back_populates="asignaciones")
    grupo: Mapped["GrupoProyecto"] = relationship(back_populates="asignaciones")
    # One-to-One
    registro_fisico: Mapped["RegistroEvaluacionFisica"] = relationship(back_populates="asignacion", uselist=False)

class RegistroEvaluacionFisica(Base):
    __tablename__ = "registro_evaluacion_fisica"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asignacion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asignacion_evaluacion.id", ondelete="CASCADE"), unique=True)
    imagen_escaneada_url: Mapped[str] = mapped_column(String(255), nullable=False)
    resultados_crudos = mapped_column(JSONB, nullable=False)
    puntaje_final = mapped_column(Numeric(5, 2), nullable=True)
    fecha_escaneo: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    asignacion: Mapped["AsignacionEvaluacion"] = relationship(back_populates="registro_fisico")