import cv2


class ProcesadorCamara:

    def __init__(
        self,
        indice: int = 0
    ):
        self.indice = indice
        self.captura = None

    def abrir(self):

        self.captura = cv2.VideoCapture(
            self.indice
        )

        if not self.captura.isOpened():
            self.captura.release()
            self.captura = None

            raise RuntimeError(
                "No se pudo abrir la cámara."
            )

        self.captura.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            1280
        )

        self.captura.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            720
        )

    def leer_frame(self):

        if self.captura is None:
            return None

        exito, frame = (
            self.captura.read()
        )

        if not exito:
            return None

        return frame

    def cerrar(self):

        if self.captura is not None:

            self.captura.release()

            self.captura = None

    def esta_abierta(self):

        return (
            self.captura is not None
            and self.captura.isOpened()
        )

    def obtener_resolucion(self):

        if self.captura is None:
            return None

        ancho = int(
            self.captura.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        alto = int(
            self.captura.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        return ancho, alto