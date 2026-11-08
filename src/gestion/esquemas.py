import uuid

from pydantic import BaseModel, SecretStr
from datetime import datetime

from typing import Literal
from pydantic import BaseModel, Field


from src.domain.rol_usuario import RolUsuario
from src.domain.conjunto_dataset import ConjuntoDataset
from src.domain.estado_entrenamiento import EstadoEntrenamiento
from src.domain.estado_revision import EstadoRevision



class LoginEntrada(BaseModel):
    nombre_usuario: str
    password: str


class UsuarioAutenticadoRespuesta(BaseModel):
    id: uuid.UUID
    nombre_usuario: str
    rol: RolUsuario

class ClaseSenalRespuesta(BaseModel):
    id: int
    codigo: int
    nombre: str
    categoria: str
    activa: bool

class LoginRespuesta(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioAutenticadoRespuesta

class DatasetCrear(BaseModel):
    nombre: str
    descripcion: str | None = None


class DatasetRespuesta(BaseModel):
    id: uuid.UUID
    nombre: str
    descripcion: str | None
    creado_por: uuid.UUID
    fecha_creacion: datetime

class ImagenDatasetRespuesta(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    nombre_archivo: str
    ancho: int
    alto: int
    conjunto: ConjuntoDataset | None
    grupo_fisico: str | None
    evidencia_id: uuid.UUID | None
    fecha_agregada: datetime

class AnotacionCrear(BaseModel):
    clase_senal_id: int

    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int


class AnotacionRespuesta(BaseModel):
    id: uuid.UUID
    imagen_id: uuid.UUID

    clase_senal_id: int
    clase_codigo: int
    clase_nombre: str

    creado_por: uuid.UUID

    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int

    fecha_creacion: datetime

class ErrorCargaImagen(BaseModel):
    nombre_archivo: str
    error: str


class CargaImagenesBulkRespuesta(BaseModel):
    cargadas: list[ImagenDatasetRespuesta]
    errores: list[ErrorCargaImagen]

class EstadisticaAnotacionesRespuesta(BaseModel):
    clase_senal_id: int
    clase_codigo: int
    clase_nombre: str
    imagenes_con_clase: int
    cantidad_anotaciones: int

class ExportacionYoloRespuesta(
    BaseModel
):
    ruta_dataset: str
    ruta_yaml: str

    imagenes_train: int
    imagenes_val: int
    imagenes_test: int

    imagenes_omitidas: int

class EntrenamientoModeloCrear(BaseModel):
    dataset_id: uuid.UUID

    version: str = Field(
        min_length=1,
        max_length=50
    )

    modelo_base: Literal[
        "yolov8n.pt",
        "yolov8s.pt",
        "yolov8m.pt",
        "yolov8l.pt",
        "yolov8x.pt",
    ] = "yolov8n.pt"

    epocas: int = Field(
        default=50,
        ge=1,
        le=500
    )

    imgsz: int = Field(
        default=640,
        ge=320,
        le=1280
    )

    batch: int = Field(
        default=8,
        ge=1,
        le=128
    )


class EntrenamientoModeloRespuesta(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    creado_por: uuid.UUID

    version: str
    modelo_base: str

    epocas: int
    imgsz: int
    batch: int

    estado: EstadoEntrenamiento
    epoca_actual: int

    mensaje_error: str | None

    fecha_creacion: datetime
    fecha_inicio: datetime | None
    fecha_fin: datetime | None

    version_modelo_id: uuid.UUID | None

class VersionModeloRespuesta(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID

    version: str
    ruta_modelo: str

    precision: float | None
    recall: float | None
    map_50: float | None
    map_50_95: float | None

    latencia_promedio_ms: float | None
    fps: float | None

    activo: bool
    fecha_entrenamiento: datetime

class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str

class DeteccionRespuesta(BaseModel):
    id: uuid.UUID

    clase_senal_id: int
    clase_nombre: str

    evidencia_id: uuid.UUID | None

    confianza: float
    fecha_hora: datetime

    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int

    latitud_captura: float | None
    longitud_captura: float | None
    distancia_estimada: float | None

    estado_revision: EstadoRevision

    version_modelo_id: uuid.UUID

    precision_ubicacion_m: float | None = None
    fecha_ubicacion: datetime | None = None
    fuente_ubicacion: str | None = None

class RevisionDeteccionCrear(BaseModel):
    resultado: EstadoRevision

    comentario: str | None = Field(
        default=None,
        max_length=500
    )


class RevisionDeteccionRespuesta(BaseModel):
    id: uuid.UUID

    deteccion_id: uuid.UUID
    usuario_id: uuid.UUID

    resultado: EstadoRevision
    comentario: str | None

    fecha_revision: datetime

class SenalRespuesta(BaseModel):
    id: uuid.UUID

    clase_senal_id: int
    clase_nombre: str

    latitud: float
    longitud: float

    estado_actual: str | None

    fecha_creacion: datetime
    fecha_actualizacion: datetime

class EstadoSenalActualizar(BaseModel):

    estado: Literal[
        "BUENO",
        "REGULAR",
        "MALO"
    ]

    comentario: str | None = Field(
        default=None,
        max_length=500
    )

class HistorialEstadoRespuesta(BaseModel):
    id: uuid.UUID
    senal_id: uuid.UUID

    usuario_id: uuid.UUID
    nombre_usuario: str

    estado_anterior: str | None
    estado_nuevo: str

    comentario: str | None

    fecha_cambio: datetime

class UsuarioGestionRespuesta(UsuarioAutenticadoRespuesta):
    activo: bool

class UsuarioGestionActualizar(BaseModel):
    rol: RolUsuario | None = None
    activo: bool | None = None

class UsuarioGestionCrear(BaseModel):
    nombre_usuario: str
    password: SecretStr
    rol: RolUsuario