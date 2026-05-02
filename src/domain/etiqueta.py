from dataclasses import dataclass
from typing import Dict


@dataclass
class Etiqueta:
    id: str
    deteccion_id: str
    bounding_box: Dict