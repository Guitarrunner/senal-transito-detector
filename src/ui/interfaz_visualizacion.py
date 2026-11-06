import uuid
import tkinter as tk
import time
import cv2
import queue

import requests

from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime


from concurrent.futures import ThreadPoolExecutor

from src.processing.procesador_imagen import ProcesadorImagen
from src.detection.detector_senales import DetectorSenales
from src.storage.cola_local import ColaLocal
from src.visualization.visualizador_resultados import VisualizadorResultados
from src.domain.usuario import Usuario
from src.gestion.cliente_api import (ClienteGestion, SesionExpiradaError)
from src.processing.procesador_camara import ProcesadorCamara
from src.detection.rastreador_temporal import RastreadorTemporal
from src.locacion.proveedor_ubicacion_macos import ProveedorUbicacionMacOS
from src.gestion.cliente_api import ErrorAPI
from src.processing.anonimizador_evidencia import AnonimizadorEvidencia
class InterfazVisualizacion:

    def __init__(self, parent, usuario_autenticado: Usuario, cliente_api: ClienteGestion):

        self.usuario_autenticado = usuario_autenticado
        self.cliente_api = cliente_api
        self.cola_local = ColaLocal()
        self.anonimizador = AnonimizadorEvidencia()
        self.sesion_expirada = False
        self.verificacion_sesion_programada = None
        self.sesion_cerrada = False

        clases = (
            self.cliente_api
            .listar_clases()
        )

        self.clases_por_nombre = {
            clase["nombre"]
            .strip()
            .lower(): clase["id"]

            for clase in clases
        }


        self.rastreador_temporal = (
            RastreadorTemporal(
                apariciones_minimas=3,
                iou_minimo=0.25,
                tiempo_expiracion=1.0
            )
        )

        self.detecciones_guardadas_sesion = 0

        self.executor_guardado = (
            ThreadPoolExecutor(
                max_workers=1
            )
        )

        self.cola_resultados_guardado = (
            queue.Queue()
        )

        self.guardados_en_proceso = 0
        self.guardado_cerrado = False

        self.verificacion_guardados_programada = None

        self.ventana = tk.Toplevel(parent)
        self.ventana.protocol(
            "WM_DELETE_WINDOW",
            self._cerrar_ventana
        )

        self.ventana.title(
            "Sistema de Reconocimiento de Señales"
        )

        self.centrar_ventana(1200, 750)

        self.imagen_tk = None
        self.imagen_actual = None
        self.detecciones_actuales = []
        self.etiquetas_actuales = []

        self.procesador = ProcesadorImagen()

        self.frames_video_actual = []
        self.indice_frame_video_actual = 0
        self.modo_video = False

        self.procesador_camara = ProcesadorCamara()

        self.proveedor_gps = ProveedorUbicacionMacOS()

        self.tiempo_frame_anterior = None
        self.fps_actual = 0.0

        self.camara_activa = False
        self.after_camara_id = None

        modelo_activo = (
            self.cliente_api
            .obtener_modelo_activo()
        )

        self.modelo_activo_id = (
            modelo_activo["id"]
        )

        self.modelo_activo_version = (
            modelo_activo["version"]
        )

        self.detector = DetectorSenales(
            modelo_path=(
                modelo_activo["ruta_modelo"]
            ),
            confianza_minima=0.35
        )

        self.visualizador = VisualizadorResultados()

        self._crear_componentes()

        try:
            self.proveedor_gps.iniciar()
        except (OSError, RuntimeError) as error:
            self.label_estado.config(
                text=f"Ubicación no disponible: {error}"
            )

        self.verificacion_guardados_programada = (
            self.ventana.after(
                100,
                self._procesar_resultados_guardado
            )
        )

        self.ventana.bind(
            "<ButtonPress>",
            self._registrar_actividad,
            add="+"
        )

        self.ventana.bind(
            "<KeyPress>",
            self._registrar_actividad,
            add="+"
        )

        self._programar_verificacion_sesion()

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

        self.boton_archivos= tk.Menubutton(
            sidebar,
            text="Archivos ▾",
            height=2,
            width=25,
            relief="raised",
            direction="below"
        )

        menu_archivos = tk.Menu(
            self.boton_archivos,
            tearoff=False
        )

        menu_archivos.add_command(
            label="Procesar imagen...",
            command=self.procesar_imagen
        )

        menu_archivos.add_command(
            label="Procesar video...",
            command=self.procesar_video
        )

        menu_archivos.add_separator()

        menu_archivos.add_command(
            label="Limpiar interfaz",
            command=self.limpiar_interfaz
        )

        self.boton_archivos.configure(
            menu=menu_archivos
        )

        self.boton_archivos.pack(
            pady=(10, 5)
        )

        self.boton_camara = tk.Button(
            sidebar,
            text="Iniciar cámara",
            command=self.alternar_camara,
            height=2,
            width=25
        )

        self.boton_camara.pack(
            pady=5
        )

        # ===== ESTADO =====

        panel_info = tk.LabelFrame(
            sidebar,
            text="Información",
            font=("Arial", 12, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )

        panel_info.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        tk.Label(
            panel_info,
            text=(
                f"Usuario: {self.usuario_autenticado.nombre_usuario}\n"
                f"Modelo: {self.modelo_activo_version}"
            ),
            bg="#f0f0f0",
            fg="#333333",
            justify="left",
            anchor="w",
            wraplength=270
        ).pack(
            fill="x",
            padx=10,
            pady=(10, 5)
        )

        self.label_estado = tk.Label(
            panel_info,
            text="Sistema listo.",
            font=("Arial", 11),
            fg="#333333",
            bg="#f0f0f0",
            justify="left",
            anchor="w",
            wraplength=270
        )

        self.label_estado.pack(
            fill="x",
            padx=10,
            pady=5
        )

        tk.Frame(
            panel_info,
            height=1,
            bg="#cccccc"
        ).pack(
            fill="x",
            padx=10,
            pady=8
        )

        contenedor_resultados = tk.Frame(
            panel_info,
            bg="#f0f0f0"
        )

        contenedor_resultados.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        self.texto_resultados = tk.Text(
            contenedor_resultados,
            height=10,
            width=32,
            wrap="word",
            state="disabled",
            relief="flat",
            fg="#333333",
            bg="#f0f0f0"
        )

        scroll_resultados = tk.Scrollbar(
            contenedor_resultados,
            command=self.texto_resultados.yview
        )

        self.texto_resultados.configure(
            yscrollcommand=scroll_resultados.set
        )

        scroll_resultados.pack(
            side="right",
            fill="y"
        )

        self.texto_resultados.pack(
            side="left",
            fill="both",
            expand=True
        )


        boton_cerrar_sesion = tk.Button(
            sidebar,
            text="Cerrar sesión",
            command=self.cerrar_sesion,
            height=2,
            width=25
        )

        boton_cerrar_sesion.pack(
            pady=10
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
        ruta = filedialog.askopenfilename(
            parent=self.ventana,
            title="Analizar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.heic *.heif"),
                ("Todos los archivos", "*")
            ]
        )

        if not ruta:
            return

        self.limpiar_interfaz()

        try:
            self.label_estado.config(
                text="Analizando imagen..."
            )
            self.ventana.update_idletasks()

            frame = self.procesador.cargar_imagen(ruta)

            detecciones, etiquetas = (
                self.detector.detectar_frame(
                    frame,
                    str(uuid.uuid4())
                )
            )

            resultado = (
                self.visualizador.dibujar_detecciones_frame(
                    frame,
                    detecciones,
                    etiquetas
                )
            )

            self.detecciones_actuales = detecciones
            self.etiquetas_actuales = etiquetas

            self._mostrar_frame_camara(resultado)
            self.mostrar_resultados(detecciones)

            self.label_estado.config(
                text=(
                    "Modo: análisis de imagen\n"
                    f"Detecciones: {len(detecciones)}\n"
                    "Resultados temporales, sin guardar."
                )
            )

        except Exception as error:
            self.label_estado.config(
                text="No se pudo analizar la imagen."
            )

            messagebox.showerror(
                "Error de análisis",
                str(error),
                parent=self.ventana
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
            (900, 650),
            Image.Resampling.LANCZOS
        )

        self.imagen_tk = ImageTk.PhotoImage(
            imagen,
            master=self.ventana
        )

        self.canvas.configure(
            image=self.imagen_tk
        )

    def limpiar_interfaz(self):
        if self.camara_activa:
            self.detener_camara()

        self.canvas.configure(image="")
        self.imagen_tk = None
        self.imagen_actual = None

        self.detecciones_actuales = []
        self.etiquetas_actuales = []

        self.frames_video_actual = []
        self.indice_frame_video_actual = 0
        self.modo_video = False

        self.frame_navegacion_video.pack_forget()

        self.texto_resultados.config(state="normal")
        self.texto_resultados.delete("1.0", tk.END)
        self.texto_resultados.config(state="disabled")

        self.label_estado.config(
            text="Sistema listo."
        )

    def procesar_video(self):
        ruta = filedialog.askopenfilename(
            parent=self.ventana,
            title="Analizar video",
            filetypes=[
                ("Videos", "*.mp4 *.avi *.mov")
            ]
        )

        if not ruta:
            return

        self.limpiar_interfaz()
        captura = None

        try:
            self.label_estado.config(
                text="Analizando video..."
            )
            self.ventana.update_idletasks()

            captura = cv2.VideoCapture(ruta)

            if not captura.isOpened():
                raise ValueError(
                    "No se pudo abrir el video."
                )

            fps = captura.get(cv2.CAP_PROP_FPS)

            if not (0 < fps < 1000):
                fps = 30.0

            intervalo = max(1, round(fps))
            indice = 0
            muestras = []
            total_detecciones = 0

            # Conservamos el muestreo anterior:
            # aproximadamente un frame por segundo,
            # con un máximo de 30 muestras.
            while len(muestras) < 30:
                exito, frame = captura.read()

                if not exito:
                    break

                if indice % intervalo == 0:
                    detecciones, etiquetas = (
                        self.detector.detectar_frame(
                            frame,
                            str(uuid.uuid4())
                        )
                    )

                    resultado = (
                        self.visualizador.dibujar_detecciones_frame(
                            frame,
                            detecciones,
                            etiquetas
                        )
                    )

                    # Guardar solo una vista reducida en RAM.
                    alto, ancho = resultado.shape[:2]
                    escala = min(
                        1.0,
                        900 / ancho,
                        650 / alto
                    )

                    if escala < 1:
                        resultado = cv2.resize(
                            resultado,
                            (
                                max(1, round(ancho * escala)),
                                max(1, round(alto * escala))
                            ),
                            interpolation=cv2.INTER_AREA
                        )

                    muestras.append({
                        "frame": indice,
                        "segundo": round(indice / fps, 2),
                        "vista": resultado,
                        "detecciones": detecciones
                    })

                    total_detecciones += len(detecciones)

                    self.label_estado.config(
                        text=(
                            "Analizando video...\n"
                            f"Muestras: {len(muestras)}"
                        )
                    )
                    self.ventana.update_idletasks()

                indice += 1

            if not muestras:
                raise ValueError(
                    "No se pudieron leer frames del video."
                )

            self.frames_video_actual = muestras
            self.indice_frame_video_actual = 0
            self.modo_video = True

            self.frame_navegacion_video.pack(pady=5)
            self.mostrar_frame_video_actual()

            self.label_estado.config(
                text=(
                    "Modo: análisis de video\n"
                    f"Muestras analizadas: {len(muestras)}\n"
                    f"Detecciones en muestras: {total_detecciones}\n"
                    "Resultados temporales, sin guardar."
                )
            )

        except Exception as error:
            self.label_estado.config(
                text="No se pudo analizar el video."
            )

            messagebox.showerror(
                "Error de análisis",
                str(error),
                parent=self.ventana
            )

        finally:
            if captura is not None:
                captura.release()

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

        frame_info = self.frames_video_actual[
            self.indice_frame_video_actual
        ]

        self._mostrar_frame_camara(
            frame_info["vista"]
        )

        self.detecciones_actuales = (
            frame_info["detecciones"]
        )

        self.mostrar_detecciones_frame_video(
            frame_info
        )

        total = len(self.frames_video_actual)

        self.label_frame_video.config(
            text=(
                f"Muestra {self.indice_frame_video_actual + 1}"
                f" de {total}"
            )
        )

        self.boton_frame_anterior.config(
            state=(
                tk.NORMAL
                if self.indice_frame_video_actual > 0
                else tk.DISABLED
            )
        )

        self.boton_frame_siguiente.config(
            state=(
                tk.NORMAL
                if self.indice_frame_video_actual < total - 1
                else tk.DISABLED
            )
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

        self.ventana.wait_window()

    def iniciar_camara(self):

        if self.camara_activa:
            return

        self.rastreador_temporal.reiniciar()

        self.detecciones_guardadas_sesion = 0

        self.frame_navegacion_video.pack_forget()

        try:
            self.procesador_camara.abrir()

        except RuntimeError as error:

            messagebox.showerror(
                "Error de cámara",
                str(error)
            )

            return

        self.boton_archivos.config(state="disabled")
        self.camara_activa = True

        self.tiempo_frame_anterior = (
            time.perf_counter()
        )

        resolucion = (
            self.procesador_camara
            .obtener_resolucion()
        )

        if resolucion is not None:
            ancho, alto = resolucion

            self.resolucion_camara = (
                f"{ancho}x{alto}"
            )
        else:
            self.resolucion_camara = (
                "Desconocida"
            )

        self.boton_camara.config(
            text="Detener cámara",
            state=tk.NORMAL
        )

        self.label_estado.config(
            text=(
                "Cámara activa\n"
                f"Modelo: "
                f"{self.modelo_activo_version}\n"
                f"Resolución: "
                f"{self.resolucion_camara}\n"
                f"GPS: "
                f"{self.proveedor_gps.estado}\n"
            )
        )

        self._actualizar_camara()

    def _actualizar_camara(self):

        if not self.camara_activa:
            return

        frame = (
            self.procesador_camara
            .leer_frame()
        )

        if frame is None:

            self.detener_camara()

            messagebox.showerror(
                "Error de cámara",
                "No se pudo obtener un frame."
            )

            return

        imagen_id = str(
            uuid.uuid4()
        )

        try:

            detecciones, etiquetas = (
                self.detector.detectar_frame(
                    frame,
                    imagen_id
                )
            )

            ubicacion = self.proveedor_gps.obtener_ubicacion()
            

            confirmadas = (
                self.rastreador_temporal
                .actualizar(
                    frame,
                    detecciones,
                    etiquetas,
                    ubicacion
                )
            )

            for candidato in confirmadas:
                self._encolar_deteccion_camara(
                    candidato
                )

            frame_resultado = (
                self.visualizador
                .dibujar_detecciones_frame(
                    frame,
                    detecciones,
                    etiquetas
                )
            )

            self._mostrar_frame_camara(
                frame_resultado
            )

            self.mostrar_resultados(
                detecciones
            )

            tiempo_actual = (
                time.perf_counter()
            )

            if (
                self.tiempo_frame_anterior
                is not None
            ):

                duracion = (
                    tiempo_actual
                    - self.tiempo_frame_anterior
                )

                if duracion > 0:
                    fps_instantaneo = (
                        1.0 / duracion
                    )

                    self.fps_actual = (
                        self.fps_actual * 0.8
                        + fps_instantaneo * 0.2
                    )

            self.tiempo_frame_anterior = (
                tiempo_actual
            )

            self.label_estado.config(
                text=(
                    "Cámara activa\n"
                    f"Modelo: "
                    f"{self.modelo_activo_version}\n"
                    f"Resolución: "
                    f"{self.resolucion_camara}\n"
                    f"FPS: "
                    f"{self.fps_actual:.1f}\n"
                    f"En frame: "
                    f"{len(detecciones)}\n"
                    f"Guardadas: "
                    f"{self.detecciones_guardadas_sesion}\n"
                    f"GPS: "
                    f"{self.proveedor_gps.estado}\n"
                )
            )

        except Exception as error:

            self.detener_camara()

            messagebox.showerror(
                "Error de inferencia",
                str(error)
            )

            return

        self.after_camara_id = (
            self.ventana.after(
                10,
                self._actualizar_camara
            )
        )

    def _mostrar_frame_camara(
        self,
        frame
    ):

        frame_rgb = (
            self.procesador
            .convertir_rgb(
                frame
            )
        )

        imagen = Image.fromarray(
            frame_rgb
        )

        imagen.thumbnail(
            (800, 600),
            Image.Resampling.LANCZOS
        )

        self.imagen_tk = (
            ImageTk.PhotoImage(
                imagen,
                master=self.ventana
            )
        )

        self.canvas.configure(
            image=self.imagen_tk
        )

    def detener_camara(self):

        self.boton_archivos.config(state="normal")
        self.camara_activa = False

        if self.after_camara_id is not None:

            try:
                self.ventana.after_cancel(
                    self.after_camara_id
                )

            except tk.TclError:
                pass

            self.after_camara_id = None

        self.procesador_camara.cerrar()

        self.canvas.configure(
            image=""
        )

        self.imagen_tk = None

        self.boton_camara.config(
            text="Iniciar cámara",
            state=tk.NORMAL
        )

        self.label_estado.config(
            text=(
                "Cámara detenida.\n"
                f"Modelo activo: "
                f"{self.modelo_activo_version}"
            )
        )

    def _cerrar_ventana(self):

        if self.camara_activa:
            self.detener_camara()

        if (
            self.verificacion_sesion_programada
            is not None
        ):
            try:
                self.ventana.after_cancel(
                    self.verificacion_sesion_programada
                )
            except tk.TclError:
                pass

            self.verificacion_sesion_programada = None

        self._cerrar_guardado_async()
        self.ventana.destroy()

    def cerrar_sesion(self):

        confirmar = messagebox.askyesno(
            "Cerrar sesión",
            "¿Desea cerrar la sesión actual?"
        )

        if not confirmar:
            return

        self.sesion_cerrada = True

        self.cliente_api.access_token = None
        self.cliente_api.sesion.close()

        self._cerrar_ventana()

    def _guardar_deteccion_camara(self, candidato):

        nombre_clase = (
            candidato.tipo_senal.strip().lower()
        )

        clase_senal_id = self.clases_por_nombre.get(
            nombre_clase
        )

        if clase_senal_id is None:
            raise ValueError(
                f"No existe la clase '{candidato.tipo_senal}' "
                "en la base de datos."
            )

        frame_anonimizado, cantidades = (
            self.anonimizador.procesar(
                candidato.mejor_frame
            )
        )

        exito, buffer = cv2.imencode(
            ".jpg",
            frame_anonimizado,
            [cv2.IMWRITE_JPEG_QUALITY, 95]
        )

        if not exito:
            raise RuntimeError(
                "No se pudo generar la evidencia."
            )

        bbox = candidato.mejor_bbox

        datos = {
            "clase_senal_id": int(clase_senal_id),
            "confianza": float(candidato.mejor_confianza),

            "bbox_x1": int(bbox["x"]),
            "bbox_y1": int(bbox["y"]),
            "bbox_x2": int(
                bbox["x"] + bbox["ancho"]
            ),
            "bbox_y2": int(
                bbox["y"] + bbox["alto"]
            ),

            "version_modelo_id": str(
                self.modelo_activo_id
            ),

            "latitud_captura": (
                float(candidato.mejor_latitud)
                if candidato.mejor_latitud is not None
                else None
            ),

            "longitud_captura": (
                float(candidato.mejor_longitud)
                if candidato.mejor_longitud is not None
                else None
            )
        }

        datos["anonimizada"] = True

        print(
            "Evidencia procesada:",
            cantidades["rostros"],
            "rostros y",
            cantidades["placas"],
            "placas cubiertas."
        )

        datos.update({
            "precision_ubicacion_m": (
                candidato.mejor_precision_ubicacion_m
            ),
            "fecha_ubicacion": (
                candidato.mejor_fecha_ubicacion.isoformat()
                if candidato.mejor_fecha_ubicacion is not None
                else None
            ),
            "fuente_ubicacion": (
                candidato.mejor_fuente_ubicacion
            )
        })

        return self.cola_local.encolar(
            usuario_id=self.usuario_autenticado.id,
            datos=datos,
            evidencia_bytes=buffer.tobytes()
        )

    def _registrar_actividad(
        self,
        event=None
    ):
        self.cliente_api.registrar_actividad()


    def _programar_verificacion_sesion(
        self
    ):
        self.verificacion_sesion_programada = (
            self.ventana.after(
                60000,
                self._verificar_sesion
            )
        )


    def _verificar_sesion(self):

        if not self.ventana.winfo_exists():
            return

        try:
            renovada = (
                self.cliente_api
                .renovar_sesion_si_necesario()
            )

            if renovada:
                print(
                    "Sesión CAMPO renovada."
                )

        except SesionExpiradaError:
            return

        except RuntimeError as error:
            print(
                "Error verificando sesión:",
                error
            )

        self._programar_verificacion_sesion()


    def cerrar_sesion_expirada(self):

        if self.sesion_expirada:
            return

        self.sesion_expirada = True

        if self.camara_activa:
            self.detener_camara()

        if (
            self.verificacion_sesion_programada
            is not None
        ):
            try:
                self.ventana.after_cancel(
                    self.verificacion_sesion_programada
                )
            except tk.TclError:
                pass

            self.verificacion_sesion_programada = None

        messagebox.showwarning(
            "Sesión expirada",
            (
                "Tu sesión ha expirado. "
                "Debes iniciar sesión nuevamente."
            )
        )

        self._cerrar_guardado_async()

        self.ventana.destroy()

    def _encolar_deteccion_camara(self, candidato):

        try:
            identificador = (
                self._guardar_deteccion_camara(candidato)
            )

        except Exception as error:
            candidato.confirmado = False

            raise RuntimeError(
                "No se pudo guardar la detección "
                "en la cola local."
            ) from error

        print(
            "Detección pendiente de envío:",
            identificador,
            candidato.tipo_senal
        )

    def _procesar_resultados_guardado(self):

        self.verificacion_guardados_programada = None

        if self.guardado_cerrado:
            return

        while True:
            try:
                futuro = (
                    self.cola_resultados_guardado
                    .get_nowait()
                )
            except queue.Empty:
                break

            self.guardados_en_proceso = 0

            try:
                resultado = futuro.result()

            except SesionExpiradaError:
                self.cerrar_sesion_expirada()
                return

            except Exception as error:
                # Por ejemplo, un problema al acceder
                # a SQLite. Detener envíos y conservar datos.
                self._cerrar_guardado_async()

                messagebox.showerror(
                    "Error de sincronización",
                    (
                        "Se detuvo el envío de pendientes.\n"
                        "Los registros no confirmados permanecen "
                        "en la cola local.\n\n"
                        f"{error}"
                    ),
                    parent=self.ventana
                )
                return

            if resultado is None:
                continue

            estado, identificador, error = resultado

            if estado == "enviado":
                self.detecciones_guardadas_sesion += 1

                print(
                    "Detección enviada:",
                    identificador
                )

            elif estado == "reintento":
                print(
                    "Detección pendiente de reintento:",
                    identificador,
                    error
                )

            else:
                print(
                    "Detección conservada para revisión:",
                    identificador,
                    error
                )

        if (
            not self.guardado_cerrado
            and self.guardados_en_proceso == 0
        ):
            futuro = self.executor_guardado.submit(
                self._enviar_siguiente_pendiente
            )

            self.guardados_en_proceso = 1

            futuro.add_done_callback(
                self.cola_resultados_guardado.put
            )

        self.verificacion_guardados_programada = (
            self.ventana.after(
                1000,
                self._procesar_resultados_guardado
            )
        )

    def _cerrar_guardado_async(self):
        self.proveedor_gps.cerrar()

        if self.guardado_cerrado:
            return

        self.guardado_cerrado = True

        if self.verificacion_guardados_programada is not None:
            try:
                self.ventana.after_cancel(
                    self.verificacion_guardados_programada
                )
            except tk.TclError:
                pass

            self.verificacion_guardados_programada = None

        self.executor_guardado.shutdown(
            wait=False,
            cancel_futures=True
        )

    def _enviar_siguiente_pendiente(self):

        if self.guardado_cerrado:
            return None

        pendiente = self.cola_local.obtener_siguiente(
            self.usuario_autenticado.id
        )

        if pendiente is None:
            return None

        identificador = pendiente["id"]

        try:
            respuesta = self.cliente_api.registrar_deteccion(
                **pendiente["datos"],
                evidencia_bytes=pendiente["evidencia"],
                id_local=identificador,
                notificar_sesion_expirada=False
            )

            # Solo borrar si la API confirma el mismo ID.
            if str(respuesta["id"]) != identificador:
                raise RuntimeError(
                    "La API devolvió un ID diferente "
                    "al de la detección enviada."
                )

        except SesionExpiradaError:
            # Mantener el pendiente para el próximo login.
            raise

        except requests.RequestException as error:
            self.cola_local.registrar_error(
                identificador,
                error,
                reintentable=True
            )

            return (
                "reintento",
                identificador,
                str(error)
            )

        except ErrorAPI as error:
            reintentable = (
                error.status_code in (408, 429)
                or 500 <= error.status_code <= 599
            )

            self.cola_local.registrar_error(
                identificador,
                error,
                reintentable=reintentable
            )

            return (
                "reintento" if reintentable else "bloqueado",
                identificador,
                str(error)
            )

        except Exception as error:
            # Conservar el registro para revisar el error.
            self.cola_local.registrar_error(
                identificador,
                error,
                reintentable=False
            )

            return (
                "bloqueado",
                identificador,
                str(error)
            )

        self.cola_local.confirmar_envio(
            identificador
        )

        return (
            "enviado",
            identificador,
            None
        )

    def alternar_camara(self):
        if self.camara_activa:
            self.detener_camara()
        else:
            self.iniciar_camara()