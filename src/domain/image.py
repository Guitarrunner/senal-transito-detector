from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Imagen:
    id: str
    ruta: str
    fecha_captura: str
    resolucion: str
    metadata: Dict = field(default_factory=dict)