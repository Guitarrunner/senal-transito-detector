from dataclasses import dataclass
from datetime import datetime


@dataclass
class UbicacionGPS:
    latitud: float
    longitud: float
    fecha_hora: datetime