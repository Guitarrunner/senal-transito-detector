import uuid
import tkinter as tk

from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime

from src.dataset.exportador_dataset import ExportadorDataset
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
        self.centrar_ventana(1200, 750)

        self.imagen_tk = None
        self.imagen_actual = None
        self.detecciones_actuales = []
        self.etiquetas_actuales = []

        self.procesador = ProcesadorImagen()

        self.detector = DetectorSenales(
            modelo_path="models/best.pt",
            confianza_minima=0.5
        )

        self.visualizador = VisualizadorResultados()

        self.almacenamiento = GestorAlmacenamiento()

        self.inicializar_exportacion_limpia()

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

        self.boton_agregar_exportacion = tk.Button(
            sidebar,
            text="Agregar a exportación",
            command=self.agregar_imagen_a_exportacion,
            height=2,
            width=25,
            state=tk.DISABLED
        )

        self.boton_agregar_exportacion.pack(
            pady=5
        )

        self.boton_exportar_dataset = tk.Button(
            sidebar,
            text="Exportar dataset YOLO",
            command=self.exportar_dataset_yolo,
            height=2,
            width=25
        )

        self.boton_exportar_dataset.pack(
            pady=5
        )

        # ===== ESTADO =====

        self.label_estado = tk.Label(
            sidebar,
            text="Esperando imagen...",
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#333333",
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
            bg="#f0f0f0",
            fg="#333333"
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
    
    def centrar_ventana(self, ancho, alto):
        self.ventana.update_idletasks()

        ancho_pantalla = self.ventana.winfo_screenwidth()
        alto_pantalla = self.ventana.winfo_screenheight()

        x = (ancho_pantalla // 2) - (ancho // 2)
        y = (alto_pantalla // 2) - (alto // 2)

        self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

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

            self.imagen_actual = imagen
            self.detecciones_actuales = detecciones
            self.etiquetas_actuales = etiquetas

            if detecciones:
                self.boton_agregar_exportacion.config(
                    state=tk.NORMAL,
                    text="Agregar a exportación"
                )
            else:
                self.boton_agregar_exportacion.config(
                    state=tk.DISABLED,
                    text="Agregar a exportación"
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

        self.imagen_actual = None
        self.detecciones_actuales = []
        self.etiquetas_actuales = []

        self.boton_agregar_exportacion.config(
            state=tk.DISABLED
        )

    def agregar_imagen_a_exportacion(self):
        if self.imagen_actual is None:
            messagebox.showwarning(
                "Sin imagen",
                "Primero debe cargar y procesar una imagen."
            )
            return

        if not self.detecciones_actuales:
            messagebox.showwarning(
                "Sin detecciones",
                "No hay detecciones para agregar a la exportación."
            )
            return

        self.almacenamiento.marcar_imagen_para_exportacion(
            self.imagen_actual.id
        )

        self.boton_agregar_exportacion.config(
            state=tk.DISABLED,
            text="Imagen agregada"
        )

        messagebox.showinfo(
            "Imagen agregada",
            "La imagen fue agregada a la cola de exportación."
        )

    def exportar_dataset_yolo(self):
        ids_aprobadas = self.almacenamiento.obtener_imagenes_para_exportacion()

        if not ids_aprobadas:
            messagebox.showwarning(
                "Sin imágenes para exportar",
                "No hay imágenes aprobadas en la cola de exportación."
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        exportador = ExportadorDataset(
            self.almacenamiento,
            export_dir=f"exports/yolo_dataset_{timestamp}"
        )

        resultado = exportador.exportar(
            solo_aprobadas=True
        )

        if resultado["imagenes_exportadas"] == 0:
            messagebox.showwarning(
                "Sin imágenes para exportar",
                "No hay imágenes aprobadas en la cola de exportación."
            )
            return

        self.limpiar_interfaz()
        self.ventana.update_idletasks()

        messagebox.showinfo(
            "Exportación completada",
            f"Imágenes exportadas: {resultado['imagenes_exportadas']}\n"
            f"Etiquetas exportadas: {resultado['etiquetas_exportadas']}\n"
            f"Ruta: {resultado['ruta_exportacion']}"
        )

    def inicializar_exportacion_limpia(self):
        """
        Limpia únicamente la cola de exportación al iniciar la aplicación.
        Las exportaciones anteriores se conservan.
        """
        self.almacenamiento.limpiar_cola_exportacion()


    def ejecutar(self):

        self.ventana.mainloop()