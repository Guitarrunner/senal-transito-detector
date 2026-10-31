import os

import requests
import mimetypes

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class ClienteGestion:

    def __init__(self, access_token: str, on_sesion_expirada=None):
        self.api_url = os.getenv(
            "GESTION_API_URL",
            "http://127.0.0.1:8000"
        )

        self.access_token = access_token
        self.on_sesion_expirada = on_sesion_expirada
        self.sesion = requests.Session()

    def _headers(self):
        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            )
        }

    def _procesar_respuesta(self, respuesta):
        if respuesta.status_code == 401:
            self.access_token = None

            if self.on_sesion_expirada:
                self.on_sesion_expirada()

            raise SesionExpiradaError(
                "La sesión expiró."
            )

        if respuesta.ok:
            return

        try:
            detalle = respuesta.json().get(
                "detail",
                "Error desconocido."
            )
        except ValueError:
            detalle = respuesta.text

        raise RuntimeError(
            f"Error {respuesta.status_code}: {detalle}"
        )

    def listar_datasets(self):
        respuesta = self.sesion.get(
            f"{self.api_url}/datasets",
            headers=self._headers(),
            timeout=10
        )

        self._procesar_respuesta(respuesta)

        return respuesta.json()

    def listar_imagenes(
        self,
        dataset_id: str
    ):
        respuesta = self.sesion.get(
            (
                f"{self.api_url}"
                f"/datasets/{dataset_id}/imagenes"
            ),
            headers=self._headers(),
            timeout=10
        )

        self._procesar_respuesta(respuesta)

        return respuesta.json()

    def obtener_imagen(
        self,
        imagen_id: str
    ) -> bytes:
        respuesta = self.sesion.get(
            (
                f"{self.api_url}"
                f"/imagenes/{imagen_id}/archivo"
            ),
            headers=self._headers(),
            timeout=20
        )

        self._procesar_respuesta(respuesta)

        return respuesta.content

    def listar_clases(self):
        respuesta = self.sesion.get(
            f"{self.api_url}/clases",
            headers=self._headers(),
            timeout=10
        )

        self._procesar_respuesta(respuesta)

        return respuesta.json()

    def listar_anotaciones(
        self,
        imagen_id: str
    ):
        respuesta = self.sesion.get(
            (
                f"{self.api_url}"
                f"/imagenes/{imagen_id}/anotaciones"
            ),
            headers=self._headers(),
            timeout=10
        )

        self._procesar_respuesta(respuesta)

        return respuesta.json()

    def crear_anotacion(
        self,
        imagen_id: str,
        clase_senal_id: int,
        bbox_x1: int,
        bbox_y1: int,
        bbox_x2: int,
        bbox_y2: int
    ):
        respuesta = self.sesion.post(
            (
                f"{self.api_url}"
                f"/imagenes/{imagen_id}/anotaciones"
            ),
            headers=self._headers(),
            json={
                "clase_senal_id": clase_senal_id,
                "bbox_x1": bbox_x1,
                "bbox_y1": bbox_y1,
                "bbox_x2": bbox_x2,
                "bbox_y2": bbox_y2
            },
            timeout=10
        )

        self._procesar_respuesta(respuesta)

        return respuesta.json()

    def eliminar_anotacion(
        self,
        imagen_id: str,
        anotacion_id: str
    ):
        respuesta = self.sesion.delete(
            (
                f"{self.api_url}"
                f"/imagenes/{imagen_id}"
                f"/anotaciones/{anotacion_id}"
            ),
            headers=self._headers(),
            timeout=10
        )

        self._procesar_respuesta(respuesta)

    def subir_imagenes_bulk(
        self,
        dataset_id: str,
        rutas_archivos
    ):
        archivos_abiertos = []

        try:
            archivos = []

            for ruta in rutas_archivos:
                ruta = Path(ruta)

                archivo = open(
                    ruta,
                    "rb"
                )

                archivos_abiertos.append(
                    archivo
                )

                tipo, _ = mimetypes.guess_type(
                    ruta.name
                )

                archivos.append(
                    (
                        "archivos",
                        (
                            ruta.name,
                            archivo,
                            tipo
                            or "application/octet-stream"
                        )
                    )
                )

            respuesta = self.sesion.post(
                (
                    f"{self.api_url}"
                    f"/datasets/{dataset_id}"
                    f"/imagenes/bulk"
                ),
                headers=self._headers(),
                files=archivos,
                timeout=300
            )

            self._procesar_respuesta(
                respuesta
            )

            return respuesta.json()

        finally:
            for archivo in archivos_abiertos:
                archivo.close()

class SesionExpiradaError(RuntimeError):
    pass