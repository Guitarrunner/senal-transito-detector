from src.domain.rol_usuario import RolUsuario
from src.domain.usuario import Usuario

class ControlAcceso:
    """
    Control de acceso básico para entorno local.
    """

    def __init__(self):
        self.usuarios = {
            "admin": {
                "id": "usuario-001",
                "password": "admin123",
                "rol": RolUsuario.ADMINISTRADOR
            },
            "operador": {
                "id": "usuario-002",
                "password": "operador123",
                "rol": RolUsuario.OPERADOR
            },
            "campo": {
                "id": "usuario-003",
                "password": "campo123",
                "rol": RolUsuario.CAMPO
            }

        }

    def autenticar(self, nombre_usuario: str, password: str):
        if nombre_usuario not in self.usuarios:
            return None

        datos_usuario = self.usuarios[nombre_usuario]

        if datos_usuario["password"] != password:
            return None

        usuario_autenticado = Usuario(
            id=datos_usuario["id"],
            nombre_usuario=nombre_usuario,
            rol=datos_usuario["rol"]
        )

        return usuario_autenticado
