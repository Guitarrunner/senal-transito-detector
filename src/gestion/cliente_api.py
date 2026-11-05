import os
import time
import jwt

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
        self.ultima_actividad = time.monotonic()

    def _headers(self):
        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            )
        }

    def _procesar_respuesta(self, respuesta, notificar_sesion_expirada=True):
        if respuesta.status_code == 401:
            self.access_token = None

            if (
                notificar_sesion_expirada
                and self.on_sesion_expirada
            ):
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

        respuesta = self._request(
            "GET",
            "/datasets"
        )

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

        respuesta = self._request(
            "GET",
            "/clases"
        )

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

    def obtener_estadisticas_anotaciones(
        self,
        dataset_id: str
    ):
        respuesta = self.sesion.get(
            (
                f"{self.api_url}"
                f"/datasets/{dataset_id}"
                f"/estadisticas-anotaciones"
            ),
            headers=self._headers(),
            timeout=10
        )

        self._procesar_respuesta(
            respuesta
        )

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

    def iniciar_entrenamiento(
        self,
        dataset_id: str,
        version: str,
        modelo_base: str,
        epocas: int,
        imgsz: int,
        batch: int
    ):
        respuesta = self._request(
            "POST",
            "/modelos/entrenamientos",
            timeout=30,
            json={
                "dataset_id": dataset_id,
                "version": version,
                "modelo_base": modelo_base,
                "epocas": epocas,
                "imgsz": imgsz,
                "batch": batch
            }
        )

        return respuesta.json()


    def listar_entrenamientos(self):

        respuesta = self._request(
            "GET",
            "/modelos/entrenamientos"
        )

        return respuesta.json()


    def obtener_entrenamiento(
        self,
        entrenamiento_id: str
    ):
        respuesta = self._request(
            "GET",
            (
                "/modelos/entrenamientos/"
                f"{entrenamiento_id}"
            )
        )

        return respuesta.json()

    def _request(
        self,
        metodo: str,
        endpoint: str,
        timeout: int = 10,
        **kwargs
    ):
        try:
            respuesta = self.sesion.request(
                method=metodo,
                url=(
                    f"{self.api_url}"
                    f"{endpoint}"
                ),
                headers=self._headers(),
                timeout=timeout,
                **kwargs
            )

        except requests.Timeout as error:
            raise RuntimeError(
                "La API tardó demasiado en responder."
            ) from error

        except requests.ConnectionError as error:
            raise RuntimeError(
                "No se pudo conectar con la API."
            ) from error

        except requests.RequestException as error:
            raise RuntimeError(
                "Ocurrió un error de comunicación con la API."
            ) from error

        self._procesar_respuesta(
            respuesta
        )

        return respuesta

    def listar_modelos(self):

        respuesta = self._request(
            "GET",
            "/modelos"
        )

        return respuesta.json()


    def activar_modelo(
        self,
        modelo_id: str
    ):

        respuesta = self._request(
            "POST",
            (
                f"/modelos/"
                f"{modelo_id}/activar"
            )
        )

        return respuesta.json()

    def registrar_actividad(self):
        self.ultima_actividad = (
            time.monotonic()
        )


    def _segundos_hasta_expirar(self):

        if not self.access_token:
            return None

        try:
            payload = jwt.decode(
                self.access_token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                }
            )

            expiracion = payload.get(
                "exp"
            )

            if expiracion is None:
                return None

            return (
                float(expiracion)
                - time.time()
            )

        except jwt.InvalidTokenError:
            return None


    def renovar_sesion_si_necesario(
        self,
        margen_segundos: int = 600,
        actividad_max_segundos: int = 600
    ) -> bool:

        # Si el usuario no ha utilizado
        # la aplicación recientemente,
        # dejamos que la sesión expire.
        tiempo_inactivo = (
            time.monotonic()
            - self.ultima_actividad
        )

        if (
            tiempo_inactivo
            > actividad_max_segundos
        ):
            return False

        segundos_restantes = (
            self._segundos_hasta_expirar()
        )

        if segundos_restantes is None:
            return False

        # Todavía falta suficiente tiempo.
        if (
            segundos_restantes
            > margen_segundos
        ):
            return False

        respuesta = self._request(
            "POST",
            "/auth/renovar"
        )

        datos = respuesta.json()

        self.access_token = (
            datos["access_token"]
        )

        return True

    def obtener_modelo_activo(self):

        respuesta = self._request(
            "GET",
            "/modelos/activo"
        )

        return respuesta.json()

    def registrar_deteccion(
        self,
        clase_senal_id: int,
        confianza: float,

        bbox_x1: int,
        bbox_y1: int,
        bbox_x2: int,
        bbox_y2: int,

        version_modelo_id: str,

        evidencia_bytes: bytes,

        latitud_captura=None,
        longitud_captura=None,
        distancia_estimada=None,

        notificar_sesion_expirada: bool = True
        ):

        datos = {
            "clase_senal_id": (
                clase_senal_id
            ),

            "confianza": confianza,

            "bbox_x1": bbox_x1,
            "bbox_y1": bbox_y1,
            "bbox_x2": bbox_x2,
            "bbox_y2": bbox_y2,

            "version_modelo_id": (
                version_modelo_id
            )
        }

        if latitud_captura is not None:
            datos["latitud_captura"] = (
                latitud_captura
            )

        if longitud_captura is not None:
            datos["longitud_captura"] = (
                longitud_captura
            )

        if distancia_estimada is not None:
            datos["distancia_estimada"] = (
                distancia_estimada
            )

        archivos = {
            "evidencia": (
                "evidencia.jpg",
                evidencia_bytes,
                "image/jpeg"
            )
        }

        respuesta = requests.post(
            (
                f"{self.api_url}"
                "/detecciones"
            ),
            headers=self._headers(),
            data=datos,
            files=archivos,
            timeout=30
        )

        self._procesar_respuesta(
            respuesta,
            notificar_sesion_expirada
        )


        return respuesta.json()

    def listar_detecciones(
        self,
        estado: str | None = None,
        senal_id: str | None = None
    ):

        parametros = {}

        if estado is not None:
            parametros["estado"] = estado

        if senal_id is not None:
            parametros["senal_id"] = (
                senal_id
            )

        respuesta = self._request(
            "GET",
            "/detecciones",
            params=parametros
        )

        return respuesta.json()

    def obtener_evidencia_deteccion(
        self,
        deteccion_id: str
    ) -> bytes:

        respuesta = self._request(
            "GET",
            (
                f"/detecciones/"
                f"{deteccion_id}/evidencia"
            ),
            timeout=20
        )

        return respuesta.content

    def revisar_deteccion(
        self,
        deteccion_id: str,
        resultado: str,
        comentario: str | None = None
    ):

        respuesta = self._request(
            "POST",
            (
                f"/detecciones/"
                f"{deteccion_id}/revision"
            ),
            json={
                "resultado": resultado,
                "comentario": comentario
            }
        )

        return respuesta.json()

    def listar_senales(
        self
    ):

        respuesta = self._request(
            "GET",
            "/senales"
        )

        return respuesta.json()

class SesionExpiradaError(RuntimeError):
    pass