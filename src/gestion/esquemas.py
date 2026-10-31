import uuid

from pydantic import BaseModel
from datetime import datetime

from src.domain.rol_usuario import RolUsuario
from src.domain.conjunto_dataset import ConjuntoDataset


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