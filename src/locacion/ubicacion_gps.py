from dataclasses import dataclass
from datetime import datetime

@dataclass
class UbicacionGPS:
    latitud: float
    longitud: float
    fecha_hora: datetime
    precision_m: float | None = None
    fuente: str | None = None