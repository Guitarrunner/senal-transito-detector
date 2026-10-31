import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.conjunto_dataset import ConjuntoDataset
from src.domain.estado_revision import EstadoRevision
from src.domain.rol_usuario import RolUsuario
from src.gestion.base_datos import Base

class UsuarioBD(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    nombre_usuario: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="rol_usuario"),
        nullable=False
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


class ClaseSenalBD(Base):
    __tablename__ = "clases_senal"

    __table_args__ = (
        UniqueConstraint(
            "codigo",
            name="uq_clases_senal_codigo"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    categoria: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    codigo: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

class EvidenciaBD(Base):
    __tablename__ = "evidencias"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ruta_archivo: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    anonimizada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

class DeteccionBD(Base):
    __tablename__ = "detecciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    clase_senal_id: Mapped[int] = mapped_column(
        ForeignKey("clases_senal.id"),
        nullable=False
    )

    evidencia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidencias.id"),
        nullable=True
    )

    confianza: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

    latitud_captura: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    longitud_captura: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    bbox_x1: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    bbox_y1: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    bbox_x2: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    bbox_y2: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    distancia_estimada: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    estado_revision: Mapped[EstadoRevision] = mapped_column(
        Enum(
            EstadoRevision,
            name="estado_revision"
        ),
        nullable=False,
        default=EstadoRevision.PENDING
    )

    senal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "senales.id",
            name="fk_detecciones_senal_id_senales"
        ),
        nullable=True
    )

    version_modelo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "versiones_modelo.id",
            name="fk_detecciones_version_modelo_id_versiones_modelo"
        ),
        nullable=False
    )

class RevisionDeteccionBD(Base):
    __tablename__ = "revisiones_deteccion"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    deteccion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("detecciones.id"),
        nullable=False
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False
    )

    resultado: Mapped[EstadoRevision] = mapped_column(
        Enum(
            EstadoRevision,
            name="estado_revision",
            create_type=False
        ),
        nullable=False
    )

    comentario: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    fecha_revision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

class SenalBD(Base):
    __tablename__ = "senales"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    clase_senal_id: Mapped[int] = mapped_column(
        ForeignKey("clases_senal.id"),
        nullable=False
    )

    latitud: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitud: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    estado_actual: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

class HistorialEstadoBD(Base):
    __tablename__ = "historial_estado"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    senal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("senales.id"),
        nullable=False
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False
    )

    estado_anterior: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    estado_nuevo: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    comentario: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    fecha_cambio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

class DatasetBD(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    descripcion: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    creado_por: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "usuarios.id",
            name="fk_datasets_creado_por_usuarios"
        ),
        nullable=False
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    
class ImagenDatasetBD(Base):
    __tablename__ = "imagenes_dataset"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "datasets.id",
            name="fk_imagenes_dataset_dataset_id_datasets"
        ),
        nullable=False
    )

    ruta_archivo: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    nombre_archivo: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    ancho: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    alto: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    conjunto: Mapped[ConjuntoDataset | None] = mapped_column(
        Enum(
            ConjuntoDataset,
            name="conjunto_dataset"
        ),
        nullable=True
    )

    grupo_fisico: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    fecha_agregada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

    evidencia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "evidencias.id",
            name="fk_imagenes_dataset_evidencia_id_evidencias"
        ),
        nullable=True
    )

class AnotacionBD(Base):
    __tablename__ = "anotaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    imagen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "imagenes_dataset.id",
            name="fk_anotaciones_imagen_id_imagenes_dataset"
        ),
        nullable=False
    )

    clase_senal_id: Mapped[int] = mapped_column(
        ForeignKey(
            "clases_senal.id",
            name="fk_anotaciones_clase_senal_id_clases_senal"
        ),
        nullable=False
    )

    creado_por: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "usuarios.id",
            name="fk_anotaciones_creado_por_usuarios"
        ),
        nullable=False
    )

    bbox_x1: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    bbox_y1: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    bbox_x2: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    bbox_y2: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

class VersionModeloBD(Base):
    __tablename__ = "versiones_modelo"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "datasets.id",
            name="fk_versiones_modelo_dataset_id_datasets"
        ),
        nullable=False
    )

    version: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    ruta_modelo: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    precision: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    recall: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    map_50: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    map_50_95: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    latencia_promedio_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    fps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    fecha_entrenamiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )