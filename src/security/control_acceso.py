class ControlAcceso:
    """
    Control de acceso básico para entorno local.
    """

    def __init__(self):
        self.usuarios = {
            "admin": {
                "password": "admin123",
                "rol": "Administrador"
            },
            "operador": {
                "password": "operador123",
                "rol": "Usuario operativo"
            }
        }

    def validar_acceso(self, usuario: str, password: str):
        if usuario not in self.usuarios:
            return False

        return self.usuarios[usuario]["password"] == password

    def obtener_rol(self, usuario: str):
        if usuario not in self.usuarios:
            return None

        return self.usuarios[usuario]["rol"]