from dataclasses import dataclass
from typing import Dict


@dataclass
class Deteccion:
    id: str
    imagen_id: str
    tipo_senal: str
    distancia: float
    ubicacion_gps: Dict
    confianza: float