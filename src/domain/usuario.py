from dataclasses import dataclass
from src.domain.rol_usuario import RolUsuario


@dataclass
class Usuario:
    id: str
    nombre_usuario: str
    rol: RolUsuario