import uuid

from pydantic import BaseModel
from datetime import datetime

from typing import Literal
from pydantic import BaseModel, Field


from src.domain.rol_usuario import RolUsuario
from src.domain.conjunto_dataset import ConjuntoDataset
from src.domain.estado_entrenamiento import EstadoEntrenamiento



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