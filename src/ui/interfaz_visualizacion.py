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
from src.processing.procesador_video import ProcesadorVideo
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

        self.procesador_video = ProcesadorVideo()
        self.imagenes_exportacion_actuales = []

        self.frames_video_actual = []
        self.indice_frame_video_actual = 0
        self.modo_video = False

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

        boton_video = tk.Button(
            sidebar,
            text="Procesar video",
            command=self.procesar_video,
            height=2,
            width=25
        )

        boton_video.pack(
            pady=5
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
            text="Esperando imagen o video...",
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

        self.frame_navegacion_video = tk.Frame(
            self.canvas.master
        )

        self.boton_frame_anterior = tk.Button(
            self.frame_navegacion_video,
            text="← Frame anterior",
            command=lambda: self.cambiar_frame_video(-1),
            width=18
        )

        self.boton_frame_anterior.pack(
            side=tk.LEFT,
            padx=5
        )

        self.label_frame_video = tk.Label(
            self.frame_navegacion_video,
            text="Frame 0 de 0",
        )

        self.label_frame_video.pack(
            side=tk.LEFT,
            padx=10
        )

        self.boton_frame_siguiente = tk.Button(
            self.frame_navegacion_video,
            text="Frame siguiente →",
            command=lambda: self.cambiar_frame_video(1),
            width=18
        )

        self.boton_frame_siguiente.pack(
            side=tk.LEFT,
            padx=5
        )

        self.frame_navegacion_video.pack(
            pady=5
        )

        self.frame_navegacion_video.pack_forget()
    
    def centrar_ventana(self, ancho, alto):
        self.ventana.update_idletasks()

        ancho_pantalla = self.ventana.winfo_screenwidth()
        alto_pantalla = self.ventana.winfo_screenheight()

        x = (ancho_pantalla // 2) - (ancho // 2)
        y = (alto_pantalla // 2) - (alto // 2)

        self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def procesar_imagen(self):

        self.modo_video = False
        self.frames_video_actual = []
        self.indice_frame_video_actual = 0

        self.frame_navegacion_video.pack_forget()

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
                self.imagenes_exportacion_actuales = [imagen.id]

                self.boton_agregar_exportacion.config(
                    state=tk.NORMAL,
                    text="Agregar a exportación"
                )
            else:
                self.imagenes_exportacion_actuales = []

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
            text="Esperando imagen o video..."
        )

        self.imagen_actual = None
        self.detecciones_actuales = []
        self.etiquetas_actuales = []

        self.boton_agregar_exportacion.config(
            state=tk.DISABLED
        )

        self.imagenes_exportacion_actuales = []

        self.boton_agregar_exportacion.config(
            state=tk.DISABLED,
            text="Agregar a exportación"
        )

        self.modo_video = False
        self.frames_video_actual = []
        self.indice_frame_video_actual = 0
        self.imagenes_exportacion_actuales = []

        self.frame_navegacion_video.pack_forget()

        self.boton_agregar_exportacion.config(
            state=tk.DISABLED,
            text="Agregar a exportación"
        )

    def agregar_imagen_a_exportacion(self):
        if not self.imagenes_exportacion_actuales:
            messagebox.showwarning(
                "Sin datos para exportar",
                "No hay imágenes o frames aprobables para agregar a la exportación."
            )
            return

        for imagen_id in self.imagenes_exportacion_actuales:
            self.almacenamiento.marcar_imagen_para_exportacion(
                imagen_id
            )

        self.boton_agregar_exportacion.config(
            state=tk.DISABLED,
            text="Agregado a exportación"
        )

        messagebox.showinfo(
            "Datos agregados",
            f"Se agregaron {len(self.imagenes_exportacion_actuales)} "
            "imagen(es) o frame(s) a la cola de exportación."
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

    def procesar_video(self):

        ruta = filedialog.askopenfilename(
            title="Seleccionar video",
            filetypes=[
                ("Videos", "*.mp4 *.avi *.mov")
            ]
        )

        if not ruta:
            return

        try:
            video_id = str(uuid.uuid4())

            self.label_estado.config(
                text="Procesando video..."
            )

            self.ventana.update_idletasks()

            resultado_video = self.procesador_video.procesar_video(
                ruta=ruta,
                video_id=video_id,
                intervalo_segundos=1,
                max_frames=30
            )

            detecciones_totales = []
            frames_con_detecciones = 0
            ruta_evidencia_mostrar = None
            resumen_frames = []
            ids_exportables = []

            for frame_info in resultado_video["frames"]:
                imagen = frame_info["imagen"]
                ruta_procesada = frame_info["ruta_procesada"]

                self.almacenamiento.guardar_imagen(
                    imagen
                )

                detecciones, etiquetas = self.detector.detectar(
                    ruta_imagen=ruta_procesada,
                    imagen_id=imagen.id
                )

                self.almacenamiento.guardar_detecciones(
                    detecciones
                )

                self.almacenamiento.guardar_etiquetas(
                    etiquetas
                )

                ruta_evidencia = self.visualizador.dibujar_detecciones(
                    ruta_imagen=ruta_procesada,
                    detecciones=detecciones,
                    etiquetas=etiquetas,
                    nombre_salida=f"{imagen.id}_evidencia.png"
                )

                if detecciones:
                    frames_con_detecciones += 1
                    detecciones_totales.extend(detecciones)
                    ids_exportables.append(imagen.id)

                    if ruta_evidencia_mostrar is None:
                        ruta_evidencia_mostrar = ruta_evidencia

                resumen_frames.append(
                    {
                        "imagen_id": imagen.id,
                        "frame": frame_info["frame"],
                        "segundo": frame_info["segundo"],
                        "ruta_evidencia": ruta_evidencia,
                        "detecciones": detecciones,
                        "etiquetas": etiquetas
                    }
                )

                self.label_estado.config(
                    text=(
                        f"Procesando video...\n"
                        f"Frames analizados: {len(resumen_frames)}"
                    )
                )

                self.ventana.update_idletasks()

            if ruta_evidencia_mostrar is None:
                ruta_evidencia_mostrar = self.visualizador.dibujar_detecciones(
                    ruta_imagen=resultado_video["frames"][0]["ruta_procesada"],
                    detecciones=[],
                    etiquetas=[],
                    nombre_salida=f"{video_id}_sin_detecciones.png"
                )

            self.imagen_actual = None
            self.detecciones_actuales = detecciones_totales
            self.etiquetas_actuales = []
            self.imagenes_exportacion_actuales = ids_exportables

            if ids_exportables:
                self.boton_agregar_exportacion.config(
                    state=tk.NORMAL,
                    text="Agregar a exportación"
                )
            else:
                self.boton_agregar_exportacion.config(
                    state=tk.DISABLED,
                    text="Agregar a exportación"
                )

            self.frames_video_actual = resumen_frames
            self.indice_frame_video_actual = 0
            self.modo_video = True

            self.frame_navegacion_video.pack(
                pady=5
            )

            self.mostrar_frame_video_actual()

            self.label_estado.config(
                text=(
                    f"Video procesado\n\n"
                    f"Frames analizados: {resultado_video['frames_analizados']}\n"
                    f"Frames con detecciones: {frames_con_detecciones}\n"
                    f"Detecciones totales: {len(detecciones_totales)}"
                )
            )

            self.label_estado.config(
                text=(
                    f"Video procesado\n\n"
                    f"Frames analizados: {resultado_video['frames_analizados']}\n"
                    f"Frames con detecciones: {frames_con_detecciones}\n"
                    f"Detecciones totales: {len(detecciones_totales)}"
                )
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error)
            )

    def mostrar_resultados_video(
        self,
        resultado_video,
        resumen_frames,
        frames_con_detecciones,
        detecciones_totales
    ):

        self.texto_resultados.config(
            state="normal"
        )

        self.texto_resultados.delete(
            "1.0",
            tk.END
        )

        texto = (
            "Análisis de video\n\n"
            f"Frames analizados: {resultado_video['frames_analizados']}\n"
            f"Frames con detecciones: {frames_con_detecciones}\n"
            f"Detecciones totales: {detecciones_totales}\n\n"
        )

        self.texto_resultados.insert(
            tk.END,
            texto
        )

        for frame_info in resumen_frames:
            detecciones = frame_info["detecciones"]

            if not detecciones:
                continue

            self.texto_resultados.insert(
                tk.END,
                f"Frame {frame_info['frame']} "
                f"({frame_info['segundo']}s)\n"
            )

            for deteccion in detecciones:
                self.texto_resultados.insert(
                    tk.END,
                    f"- {deteccion.tipo_senal} "
                    f"({deteccion.confianza:.2f})\n"
                )

            self.texto_resultados.insert(
                tk.END,
                "\n"
            )

        if detecciones_totales == 0:
            self.texto_resultados.insert(
                tk.END,
                "No se detectaron señales en los frames analizados."
            )

        self.texto_resultados.config(
            state="disabled"
        )

    def cambiar_frame_video(self, direccion):
        if not self.frames_video_actual:
            return

        nuevo_indice = self.indice_frame_video_actual + direccion

        if nuevo_indice < 0:
            nuevo_indice = 0

        if nuevo_indice >= len(self.frames_video_actual):
            nuevo_indice = len(self.frames_video_actual) - 1

        self.indice_frame_video_actual = nuevo_indice
        self.mostrar_frame_video_actual()

    def mostrar_frame_video_actual(self):
        if not self.frames_video_actual:
            return

        frame_info = self.frames_video_actual[self.indice_frame_video_actual]

        self.mostrar_imagen(
            frame_info["ruta_evidencia"]
        )

        self.mostrar_detecciones_frame_video(
            frame_info
        )

        total_frames = len(self.frames_video_actual)
        frame_actual = self.indice_frame_video_actual + 1

        self.label_frame_video.config(
            text=f"Frame {frame_actual} de {total_frames}"
        )

        self.boton_frame_anterior.config(
            state=tk.NORMAL if self.indice_frame_video_actual > 0 else tk.DISABLED
        )

        self.boton_frame_siguiente.config(
            state=(
                tk.NORMAL
                if self.indice_frame_video_actual < total_frames - 1
                else tk.DISABLED
            )
        )

        detecciones = frame_info["detecciones"]

        if detecciones:
            self.imagenes_exportacion_actuales = [
                frame_info["imagen_id"]
            ]

            self.boton_agregar_exportacion.config(
                state=tk.NORMAL,
                text="Agregar a exportación"
            )
        else:
            self.imagenes_exportacion_actuales = []

            self.boton_agregar_exportacion.config(
                state=tk.DISABLED,
                text="Agregar a exportación"
            )

    def mostrar_detecciones_frame_video(self, frame_info):
        self.texto_resultados.config(
            state="normal"
        )

        self.texto_resultados.delete(
            "1.0",
            tk.END
        )

        detecciones = frame_info["detecciones"]

        encabezado = (
            "Detecciones del frame actual\n\n"
            f"Frame original: {frame_info['frame']}\n"
            f"Segundo aproximado: {frame_info['segundo']}s\n"
            f"Detecciones encontradas: {len(detecciones)}\n\n"
        )

        self.texto_resultados.insert(
            tk.END,
            encabezado
        )

        if not detecciones:
            self.texto_resultados.insert(
                tk.END,
                "No se detectaron señales en este frame."
            )
        else:
            for indice, deteccion in enumerate(detecciones, start=1):
                self.texto_resultados.insert(
                    tk.END,
                    f"Detección {indice}\n"
                )

                self.texto_resultados.insert(
                    tk.END,
                    f"Tipo: {deteccion.tipo_senal}\n"
                )

                self.texto_resultados.insert(
                    tk.END,
                    f"Confianza: {deteccion.confianza:.2f}\n\n"
                )

        self.texto_resultados.config(
            state="disabled"
        )

    def ejecutar(self):

        self.ventana.mainloop()