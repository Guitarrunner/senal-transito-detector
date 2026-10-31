import os

import requests
from dotenv import load_dotenv

from src.domain.rol_usuario import RolUsuario
from src.domain.usuario import Usuario


load_dotenv()

class ControlAcceso:
    """
    Control de acceso básico para entorno local.
    """

    def __init__(self):
        self.api_url = os.getenv(
            "GESTION_API_URL",
            "http://127.0.0.1:8000"
        )

        self.access_token = None
        

    def autenticar(
        self,
        nombre_usuario: str,
        password: str
    ) -> Usuario | None:

        try:
            respuesta = requests.post(
                f"{self.api_url}/auth/login",
                json={
                    "nombre_usuario": nombre_usuario,
                    "password": password
                },
                timeout=5
            )

        except requests.RequestException as error:
            raise RuntimeError(
                "No se pudo conectar con la API de gestión."
            ) from error

        if respuesta.status_code == 401:
            return None

        respuesta.raise_for_status()

        datos = respuesta.json()

        self.access_token = datos["access_token"]

        datos_usuario = datos["usuario"]
        
        return Usuario(
            id=str(datos_usuario["id"]),
            nombre_usuario=datos_usuario["nombre_usuario"],
            rol=RolUsuario(
                datos_usuario["rol"]
            )
)