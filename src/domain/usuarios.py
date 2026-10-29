from dataclasses import dataclass
from typing import Dict
from rolUsuario import RolUsuario


@dataclass
class Usuario:
    id: str
    nombre_usuario: str
    rol: RolUsuario