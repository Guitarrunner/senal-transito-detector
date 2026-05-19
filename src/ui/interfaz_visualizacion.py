import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import uuid
from datetime import datetime

from src.processing.procesador_imagen import ProcesadorImagen
from src.detection.detector_senales import DetectorSenales
from src.visualization.visualizador_resultados import VisualizadorResultados
from src.storage.gestor_almacenamiento import GestorAlmacenamiento


class InterfazVisualizacion:

    def __init__(self):

        self.ventana = tk.Tk()

        self.ventana.title(
            "Sistema de Reconocimiento de Señales"
        )

        self.ventana.geometry("1200x750")

        self.imagen_tk = None

        self.procesador = ProcesadorImagen()

        self.detector = DetectorSenales(
            confianza_minima=0.3
        )

        self.visualizador = VisualizadorResultados()

        self.almacenamiento = GestorAlmacenamiento()

        self._crear_componentes()

    def _crear_componentes(self):

        # ===== HEADER =====

        header = tk.Frame(
            self.ventana,
            bg="#202020",
            height=70
        )

        header.pack(
            fill="x"
        )

        titulo = tk.Label(
            header,
            text="Sistema de Reconocimiento de Señales",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#202020"
        )

        titulo.pack(
            pady=15
        )

        # ===== MAIN =====

        main_frame = tk.Frame(self.ventana)

        main_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # ===== SIDEBAR =====

        sidebar = tk.Frame(
            main_frame,
            width=320,
            bg="#f0f0f0"
        )

        sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )

        # ===== BOTONES =====

        boton_cargar = tk.Button(
            sidebar,
            text="Procesar imagen",
            command=self.procesar_imagen,
            height=2,
            width=25
        )

        boton_cargar.pack(
            pady=10
        )

        boton_limpiar = tk.Button(
            sidebar,
            text="Limpiar interfaz",
            command=self.limpiar_interfaz,
            height=2,
            width=25
        )

        boton_limpiar.pack(
            pady=5
        )

        # ===== ESTADO =====

        self.label_estado = tk.Label(
            sidebar,
            text="Esperando imagen...",
            font=("Arial", 11),
            bg="#f0f0f0",
            wraplength=280,
            justify="left"
        )

        self.label_estado.pack(
            pady=10
        )

        # ===== RESULTADOS =====

        titulo_resultados = tk.Label(
            sidebar,
            text="Detecciones",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        )

        titulo_resultados.pack(
            pady=(20, 5)
        )

        self.texto_resultados = tk.Text(
            sidebar,
            height=25,
            width=35,
            state="disabled"
        )

        self.texto_resultados.pack(
            pady=5,
            padx=10
        )

        # ===== VISUALIZADOR =====

        viewer = tk.Frame(main_frame)

        viewer.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.canvas = tk.Label(viewer)

        self.canvas.pack(
            pady=10
        )

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

            self.ventana.update()

            resultado = self.procesador.procesar_imagen(
                ruta=ruta,
                imagen_id=imagen_id
            )

            imagen = resultado["imagen"]

            ruta_procesada = resultado[
                "ruta_procesada"
            ]

            detecciones, etiquetas = (
                self.detector.detectar(
                    ruta_imagen=ruta_procesada,
                    imagen_id=imagen.id
                )
            )

            ruta_evidencia = (
                self.visualizador.dibujar_detecciones(
                    ruta_imagen=ruta_procesada,
                    detecciones=detecciones,
                    etiquetas=etiquetas,
                    nombre_salida=f"{imagen.id}_evidencia.png"
                )
            )

            self.almacenamiento.guardar_imagen(
                imagen
            )

            self.almacenamiento.guardar_detecciones(
                detecciones
            )

            self.almacenamiento.guardar_etiquetas(
                etiquetas
            )

            self.mostrar_imagen(
                ruta_evidencia
            )

            self.mostrar_resultados(
                detecciones
            )

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            self.label_estado.config(
                text=(
                    f"Procesamiento completado\n\n"
                    f"Detecciones: {len(detecciones)}\n"
                    f"Fecha: {timestamp}"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    def mostrar_resultados(
        self,
        detecciones
    ):

        self.texto_resultados.config(
            state="normal"
        )

        self.texto_resultados.delete(
            "1.0",
            tk.END
        )

        if not detecciones:

            self.texto_resultados.insert(
                tk.END,
                "No se detectaron objetos."
            )

        else:

            for index, deteccion in enumerate(
                detecciones,
                start=1
            ):

                texto = (
                    f"Detección #{index}\n"
                    f"Tipo: {deteccion.tipo_senal}\n"
                    f"Confianza: "
                    f"{deteccion.confianza:.2f}\n\n"
                )

                self.texto_resultados.insert(
                    tk.END,
                    texto
                )

        self.texto_resultados.config(
            state="disabled"
        )

    def mostrar_imagen(
        self,
        ruta_imagen
    ):

        imagen = Image.open(
            ruta_imagen
        )

        imagen.thumbnail(
            (800, 600)
        )

        self.imagen_tk = ImageTk.PhotoImage(
            imagen
        )

        self.canvas.configure(
            image=self.imagen_tk
        )

    def limpiar_interfaz(self):

        self.canvas.configure(
            image=""
        )

        self.texto_resultados.config(
            state="normal"
        )

        self.texto_resultados.delete(
            "1.0",
            tk.END
        )

        self.texto_resultados.config(
            state="disabled"
        )

        self.label_estado.config(
            text="Esperando imagen..."
        )

    def ejecutar(self):

        self.ventana.mainloop()