from dataclasses import dataclass


@dataclass
class Senal:
    id: str
    nombre: str
    tipo: str
    descripcion: str = ""