import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import uuid

from src.processing.procesador_imagen import ProcesadorImagen
from src.detection.detector_senales import DetectorSenales
from src.visualization.visualizador_resultados import VisualizadorResultados
from src.storage.gestor_almacenamiento import GestorAlmacenamiento
class InterfazVisualizacion:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title(
            "Sistema de Reconocimiento de Señales de Tránsito"
        )

        self.ventana.geometry("1000x700")

        self.imagen_tk = None

        self.procesador = ProcesadorImagen()
        self.detector = DetectorSenales(confianza_minima=0.3)
        self.visualizador = VisualizadorResultados()
        self.almacenamiento = GestorAlmacenamiento()

        self._crear_componentes()

    def _crear_componentes(self):

        titulo = tk.Label(
            self.ventana,
            text="Sistema de Reconocimiento de Señales",
            font=("Arial", 20, "bold")
        )

        titulo.pack(pady=10)

        boton = tk.Button(
            self.ventana,
            text="Seleccionar imagen",
            command=self.procesar_imagen,
            height=2,
            width=25
        )

        boton.pack(pady=10)

        self.label_estado = tk.Label(
            self.ventana,
            text="Esperando imagen...",
            font=("Arial", 11)
        )

        self.label_estado.pack(pady=5)

        self.label_resultados = tk.Label(
            self.ventana,
            text="",
            font=("Arial", 11),
            justify="left"
        )

        self.label_resultados.pack(pady=5)

        self.canvas = tk.Label(self.ventana)

        self.canvas.pack(pady=10)

    def procesar_imagen(self):

        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png")
            ]
        )

        if not ruta:
            return

        try:

            imagen_id = str(uuid.uuid4())

            self.label_estado.config(
                text="Procesando imagen..."
            )

            resultado = self.procesador.procesar_imagen(
                ruta=ruta,
                imagen_id=imagen_id
            )

            imagen = resultado["imagen"]
            ruta_procesada = resultado["ruta_procesada"]

            detecciones, etiquetas = self.detector.detectar(
                ruta_imagen=ruta_procesada,
                imagen_id=imagen.id
            )

            ruta_evidencia = self.visualizador.dibujar_detecciones(
                ruta_imagen=ruta_procesada,
                detecciones=detecciones,
                etiquetas=etiquetas,
                nombre_salida=f"{imagen.id}_evidencia.png"
            )

            self.almacenamiento.guardar_imagen(imagen)
            self.almacenamiento.guardar_detecciones(detecciones)
            self.almacenamiento.guardar_etiquetas(etiquetas)

            self.mostrar_imagen(ruta_evidencia)

            texto = (
                f"Imagen procesada correctamente\n"
                f"Detecciones: {len(detecciones)}\n"
                f"Ruta evidencia:\n{ruta_evidencia}"
            )

            self.label_estado.config(
                text="Procesamiento completado"
            )

            self.label_resultados.config(
                text=texto
            )

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    def mostrar_imagen(self, ruta_imagen):

        imagen = Image.open(ruta_imagen)

        imagen.thumbnail((850, 500))

        self.imagen_tk = ImageTk.PhotoImage(imagen)

        self.canvas.configure(
            image=self.imagen_tk
        )

    def ejecutar(self):
        self.ventana.mainloop()