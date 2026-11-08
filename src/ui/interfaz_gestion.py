import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkintermapview import TkinterMapView

from pathlib import Path
from io import BytesIO

from PIL import (
    Image,
    ImageTk,
    ImageDraw
)

from src.domain.usuario import Usuario
from src.domain.rol_usuario import RolUsuario
from src.gestion.cliente_api import (ClienteGestion, SesionExpiradaError)
from src.ui.etiquetador_dataset import EtiquetadorDataset
from src.ui.gestion_modelos import GestionModelos

class InterfazGestion:

    def __init__(
            self,
            parent,
            usuario_autenticado: Usuario,
            cliente_api: ClienteGestion
        ):

        self.usuario_autenticado = usuario_autenticado
        self.cliente_api = cliente_api
        self.sesion_expirada = False
        self.sesion_cerrada = False

        self.contenido_actual = None
        self.detecciones_pendientes = {}
        self.imagen_evidencia_tk = None
        self.deteccion_seleccionada_id = None
        self.senal_seleccionada_id = None

        self.ventana = tk.Toplevel(parent)

        self.ventana.title(
            "Sistema de Gestión de Señales"
        )

        self.centrar_ventana(1400,850)

        self._crear_componentes()

        self.verificacion_sesion_programada = None

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
            text="Sistema de Gestión de Señales",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#202020"
        )

        titulo.pack(
            pady=15
        )


        # ===== MAIN =====

        main_frame = tk.Frame(
            self.ventana
        )

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

        # ===== BOTONES PRINCIPALES =====

        boton_detecciones = tk.Button(
            sidebar,
            text="Detecciones pendientes",
            command=self.mostrar_detecciones,
            height=2,
            width=25
        )

        boton_detecciones.pack(
            pady=5
        )


        boton_inventario = tk.Button(
            sidebar,
            text="Inventario",
            command=self.mostrar_inventario,
            height=2,
            width=25
        )

        boton_inventario.pack(
            pady=5
        )


        boton_mapa = tk.Button(
            sidebar,
            text="Mapa",
            command=self.mostrar_mapa,
            height=2,
            width=25
        )

        boton_mapa.pack(
            pady=5
        )

        self.botones_vistas = {
            "detecciones": boton_detecciones,
            "inventario": boton_inventario,
            "mapa": boton_mapa
        }

        # ===== FUNCIONES ADMINISTRADOR =====

        if (
            self.usuario_autenticado.rol
            == RolUsuario.ADMINISTRADOR
        ):
            self._crear_componentes_administrador(
                sidebar
            )


        # ===== ESTADO =====

        self.label_estado = tk.Label(
            sidebar,
            text="Sistema de gestión listo.",
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#333333",
            wraplength=280,
            justify="left"
        )

        self.label_estado.pack(
            pady=20
        )

        boton_cerrar_sesion = tk.Button(
            sidebar,
            text="Cerrar sesión",
            command=self.cerrar_sesion,
            height=2,
            width=25
        )

        boton_cerrar_sesion.pack(
            side="bottom",
            pady=15
        )

        # ===== ÁREA DE CONTENIDO =====

        self.frame_contenido = tk.Frame(
            main_frame
        )

        self.frame_contenido.pack(
            side="right",
            fill="both",
            expand=True
        )


        self.titulo_contenido = tk.Label(
            self.frame_contenido,
            text="",
            font=("Arial", 20, "bold")
        )

        self.titulo_contenido.pack(
            pady=20
        )

        self.texto_contenido = tk.Label(
            self.frame_contenido,
            text=(
                "Seleccione una opción del menú "
                "para comenzar."
            ),
            font=("Arial", 12)
        )

        self.texto_contenido.pack(
            pady=10
        )


    def _crear_componentes_administrador(
        self,
        sidebar
    ):

        separador = tk.Label(
            sidebar,
            text="Administración",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )

        separador.pack(
            pady=(25, 5)
        )


        boton_usuarios = tk.Button(
            sidebar,
            text="Usuarios",
            command=self.mostrar_usuarios,
            height=2,
            width=25
        )

        boton_usuarios.pack(
            pady=5
        )


        boton_modelos = tk.Button(
            sidebar,
            text="Modelos",
            command=self.mostrar_modelos,
            height=2,
            width=25
        )

        boton_modelos.pack(
            pady=5
        )


        boton_dataset = tk.Button(
            sidebar,
            text="Dataset",
            command=self.mostrar_dataset,
            height=2,
            width=25
        )

        boton_dataset.pack(
            pady=5
        )

        self.botones_vistas.update({
            "usuarios": boton_usuarios,
            "dataset": boton_dataset,
            "modelos": boton_modelos,
        })

    def centrar_ventana(
        self,
        ancho,
        alto
    ):

        self.ventana.update_idletasks()

        ancho_pantalla = (
            self.ventana.winfo_screenwidth()
        )

        alto_pantalla = (
            self.ventana.winfo_screenheight()
        )

        x = (
            (ancho_pantalla // 2)
            - (ancho // 2)
        )

        y = (
            (alto_pantalla // 2)
            - (alto // 2)
        )

        self.ventana.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )


    def mostrar_detecciones(self):

        self._limpiar_contenido_actual()
        self._marcar_vista_activa("detecciones")

        self.titulo_contenido.config(
            text="Detecciones pendientes"
        )

        self.texto_contenido.pack_forget()

        self.label_estado.config(
            text="Consultando detecciones..."
        )

        try:
            detecciones = (
                self.cliente_api
                .listar_detecciones(
                    estado="PENDING"
                )
            )

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            return

        self.detecciones_pendientes = {
            str(deteccion["id"]): deteccion
            for deteccion in detecciones
        }

        self.contenido_actual = tk.Frame(
            self.frame_contenido
        )

        self.contenido_actual.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        if not detecciones:

            mensaje = tk.Label(
                self.contenido_actual,
                text=(
                    "No hay detecciones "
                    "pendientes de revisión."
                ),
                font=("Arial", 12)
            )

            mensaje.pack(
                pady=40
            )

            self.label_estado.config(
                text="Sin detecciones pendientes."
            )

            return

        frame_lista = tk.Frame(
            self.contenido_actual
        )


        contenedor_detalle = tk.Frame(
            self.contenido_actual,
            bd=1,
            relief="solid",
        )

        paneles = ttk.Panedwindow(self.contenido_actual, orient=tk.VERTICAL)
        paneles.pack(fill="both", expand=True)

        frame_lista = ttk.Frame(paneles)
        contenedor_detalle = ttk.Frame(paneles)

        paneles.add(frame_lista, weight=1)
        paneles.add(contenedor_detalle, weight=2)


        canvas_detalle = tk.Canvas(
            contenedor_detalle,
            highlightthickness=0,
            width=1,
        )

        scroll_detalle = ttk.Scrollbar(
            contenedor_detalle,
            orient="vertical",
            command=canvas_detalle.yview
        )

        canvas_detalle.configure(
            yscrollcommand=scroll_detalle.set
        )


        scroll_detalle.pack(
            side="right",
            fill="y"
        )

        canvas_detalle.pack(
            side="left",
            fill="both",
            expand=True
        )


        frame_detalle = tk.Frame(
            canvas_detalle
        )

        self.mensaje_sin_deteccion = tk.Label(
            frame_detalle,
            text="Seleccione una detección para ver su evidencia.",
            font=("Arial", 12),
        )
        self.mensaje_sin_deteccion.pack(pady=35)

        self.vista_detalle_deteccion = tk.Frame(frame_detalle)

        ventana_detalle = (
            canvas_detalle.create_window(
                (0, 0),
                window=frame_detalle,
                anchor="nw"
            )
        )

        def actualizar_scroll(event):
            canvas_detalle.configure(
                scrollregion=canvas_detalle.bbox("all")
            )

        def ajustar_ancho(event):
            canvas_detalle.itemconfigure(
                ventana_detalle,
                width=event.width
            )

        frame_detalle.bind(
            "<Configure>",
            actualizar_scroll
        )

        canvas_detalle.bind(
            "<Configure>",
            ajustar_ancho
        )

        columnas = (
            "clase",
            "confianza",
            "fecha",
            "estado"
        )

        tabla = ttk.Treeview(
            frame_lista,
            columns=columnas,
            show="headings",
            height=3
        )

        tabla.heading(
            "clase",
            text="Clase"
        )

        tabla.heading(
            "confianza",
            text="Confianza"
        )

        tabla.heading(
            "fecha",
            text="Fecha"
        )

        tabla.heading(
            "estado",
            text="Estado"
        )

        tabla.column(
            "clase",
            width=60
        )

        tabla.column(
            "confianza",
            width=60,
            anchor="center"
        )

        tabla.column(
            "fecha",
            width=160,
            anchor="center"
        )

        tabla.column(
            "estado",
            width=90,
            anchor="center"
        )

        scrollbar = ttk.Scrollbar(
            frame_lista,
            orient="vertical",
            command=tabla.yview
        )

        titulo_detalle = tk.Label(
            self.vista_detalle_deteccion,
            text="Detalle de detección",
            font=("Arial", 16, "bold")
        )

        titulo_detalle.pack(
            pady=(15, 5)
        )

        fila_detalle = tk.Frame(self.vista_detalle_deteccion)
        fila_detalle.pack(fill="x", padx=20, pady=(0, 15))

        fila_detalle.columnconfigure(0, weight=1)
        fila_detalle.columnconfigure(1, weight=1)

        self.frame_foto = tk.Frame(fila_detalle)
        self.frame_foto.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        frame_info = tk.Frame(fila_detalle)
        frame_info.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self.label_evidencia = tk.Label(
            self.frame_foto,
            text=(
                ""
            )
        )

        self.label_evidencia.pack(
            pady=15
        )


        self.label_detalle_deteccion = tk.Label(
            frame_info,
            text="",
            font=("Arial", 11),
            justify="left",
            anchor="w",
        )

        self.label_detalle_deteccion.pack(
            fill="x",
            padx=25,
            pady=10
        )

        frame_botones = tk.Frame(
            frame_info
        )

        frame_botones.pack(
            pady=20
        )


        self.boton_aprobar = tk.Button(
            frame_botones,
            text="Aprobar",
            command=self._aprobar_deteccion,
            width=15,
            height=2,
            state="disabled"
        )

        self.boton_rechazar = tk.Button(
            frame_botones,
            text="Rechazar",
            command=self._rechazar_deteccion,
            width=15,
            height=2,
            state="disabled"
        )

        frame_botones.columnconfigure(0, weight=1, uniform="revision")
        frame_botones.columnconfigure(1, weight=1, uniform="revision")

        self.boton_aprobar.grid(row=0, column=0, sticky="ew", padx=10)
        self.boton_rechazar.grid(row=0, column=1, sticky="ew", padx=10)

        tabla.configure(
            yscrollcommand=scrollbar.set
        )

        tabla.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        for deteccion in detecciones:

            fecha = (
                deteccion["fecha_hora"]
                .replace("T", " ")
                [:19]
            )

            confianza = (
                f"{deteccion['confianza'] * 100:.1f}%"
            )

            tabla.insert(
                "",
                tk.END,
                iid=str(
                    deteccion["id"]
                ),
                values=(
                    deteccion[
                        "clase_nombre"
                    ],
                    confianza,
                    fecha,
                    deteccion[
                        "estado_revision"
                    ]
                )
            )

        self.tabla_detecciones = tabla

        self.tabla_detecciones.bind(
            "<<TreeviewSelect>>",
            self._mostrar_detalle_deteccion
        )

        self.label_estado.config(
            text=(
                f"Detecciones pendientes: "
                f"{len(detecciones)}"
            )
        )

    def _mostrar_detalle_deteccion(
        self,
        event=None
    ):

        seleccion = (
            self.tabla_detecciones
            .selection()
        )

        if not seleccion:
            return

        deteccion_id = seleccion[0]

        self.deteccion_seleccionada_id = (
            deteccion_id
        )

        deteccion = (
            self.detecciones_pendientes
            .get(
                deteccion_id
            )
        )

        if deteccion is None:
            return

        self.label_estado.config(
            text="Cargando evidencia..."
        )

        try:

            evidencia_bytes = (
                self.cliente_api
                .obtener_evidencia_deteccion(
                    deteccion_id
                )
            )

            imagen = Image.open(
                BytesIO(
                    evidencia_bytes
                )
            ).convert("RGB")

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            return
            
        dibujo = ImageDraw.Draw(
            imagen
        )

        bbox = (
            deteccion["bbox_x1"],
            deteccion["bbox_y1"],
            deteccion["bbox_x2"],
            deteccion["bbox_y2"]
        )

        grosor = max(
            2,
            imagen.width // 300
        )

        dibujo.rectangle(
            bbox,
            outline="red",
            width=grosor
        )

        self.mensaje_sin_deteccion.pack_forget()
        self.vista_detalle_deteccion.pack(fill="x")
        self.vista_detalle_deteccion.update_idletasks()

        ancho_foto = max(1, self.frame_foto.winfo_width() - 20)
        imagen.thumbnail(
            (min(600, ancho_foto), 520),
            Image.Resampling.LANCZOS,
        )

        self.imagen_evidencia_tk = (
            ImageTk.PhotoImage(
                imagen
            )
        )

        self.label_evidencia.config(
            image=self.imagen_evidencia_tk,
            text=""
        )

        self.label_evidencia.image = (
            self.imagen_evidencia_tk
        )

        fecha = (
            deteccion["fecha_hora"]
            .replace("T", " ")
            [:19]
        )

        confianza = (
            deteccion["confianza"]
            * 100
        )

        latitud = (
            deteccion[
                "latitud_captura"
            ]
        )

        longitud = (
            deteccion[
                "longitud_captura"
            ]
        )

        if (
            latitud is not None
            and longitud is not None
        ):

            ubicacion = (
                f"{latitud:.6f}, "
                f"{longitud:.6f}"
            )

        else:

            ubicacion = "Sin GPS"

        texto = (
            f"Clase: "
            f"{deteccion['clase_nombre']}\n\n"

            f"Confianza: "
            f"{confianza:.1f}%\n\n"

            f"Fecha: "
            f"{fecha}\n\n"

            f"Estado: "
            f"{deteccion['estado_revision']}\n\n"

            f"Ubicación: "
            f"{ubicacion}\n\n"

            f"Bounding box: "
            f"({deteccion['bbox_x1']}, "
            f"{deteccion['bbox_y1']}) → "
            f"({deteccion['bbox_x2']}, "
            f"{deteccion['bbox_y2']})"
        )

        self.label_detalle_deteccion.config(
            text=texto
        )

        self.mensaje_sin_deteccion.pack_forget()
        self.vista_detalle_deteccion.pack(fill="x")

        self.label_estado.config(
            text=(
                "Detección seleccionada: "
                f"{deteccion['clase_nombre']}"
            )
        )

        self.boton_aprobar.config(
            state="normal"
        )

        self.boton_rechazar.config(
            state="normal"
        )

    def mostrar_inventario(self, *, senal_id=None):

        self._limpiar_contenido_actual()
        self._marcar_vista_activa("inventario")

        self.titulo_contenido.config(
            text="Inventario"
        )

        self.texto_contenido.pack_forget()

        self.label_estado.config(
            text="Consultando inventario..."
        )

        try:

            senales = (
                self.cliente_api
                .listar_senales()
            )

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            return

        self.contenido_actual = tk.Frame(
            self.frame_contenido
        )

        self.contenido_actual.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        if not senales:

            mensaje = tk.Label(
                self.contenido_actual,
                text=(
                    "No hay señales registradas "
                    "en el inventario."
                ),
                font=("Arial", 12)
            )

            mensaje.pack(
                pady=40
            )

            self.label_estado.config(
                text="Inventario vacío."
            )

            return

        frame_lista = tk.Frame(
            self.contenido_actual
        )

        contenedor_detalle = tk.Frame(
            self.contenido_actual,
            bd=1,
            relief="solid"
        )

        paneles = ttk.Panedwindow(self.contenido_actual, orient=tk.VERTICAL)
        paneles.pack(fill="both", expand=True)

        frame_lista = ttk.Frame(paneles)
        contenedor_detalle = ttk.Frame(paneles)

        paneles.add(frame_lista, weight=1)
        paneles.add(contenedor_detalle, weight=2)

        canvas_detalle = tk.Canvas(
            contenedor_detalle,
            width=1,
            highlightthickness=0
        )

        scroll_detalle = ttk.Scrollbar(
            contenedor_detalle,
            orient="vertical",
            command=canvas_detalle.yview
        )

        canvas_detalle.configure(
            yscrollcommand=scroll_detalle.set
        )

        scroll_detalle.pack(
            side="right",
            fill="y"
        )

        canvas_detalle.pack(
            side="left",
            fill="both",
            expand=True
        )

        frame_detalle = tk.Frame(canvas_detalle)

        ventana_detalle = canvas_detalle.create_window(
            (0, 0),
            window=frame_detalle,
            anchor="nw"
        )

        def actualizar_scroll(event):
            canvas_detalle.configure(
                scrollregion=canvas_detalle.bbox("all")
            )

        def ajustar_ancho(event):
            canvas_detalle.itemconfigure(
                ventana_detalle,
                width=event.width
            )

        frame_detalle.bind(
            "<Configure>",
            actualizar_scroll
        )

        canvas_detalle.bind(
            "<Configure>",
            ajustar_ancho
        )

        columnas = (
            "clase",
            "latitud",
            "longitud",
            "estado",
            "actualizacion"
        )

        tabla = ttk.Treeview(
            frame_lista,
            columns=columnas,
            show="headings",
            height=2
        )

        tabla.heading(
            "clase",
            text="Clase"
        )

        tabla.heading(
            "latitud",
            text="Latitud"
        )

        tabla.heading(
            "longitud",
            text="Longitud"
        )

        tabla.heading(
            "estado",
            text="Estado"
        )

        tabla.heading(
            "actualizacion",
            text="Última actualización"
        )

        tabla.column(
            "clase",
            width=80
        )

        tabla.column(
            "latitud",
            width=80,
            anchor="center"
        )

        tabla.column(
            "longitud",
            width=80,
            anchor="center"
        )

        tabla.column(
            "estado",
            width=80,
            anchor="center"
        )

        tabla.column(
            "actualizacion",
            width=180,
            anchor="center"
        )

        self.senales_inventario = {
            str(senal["id"]): senal
            for senal in senales
        }

        titulo_detalle = tk.Label(
            frame_detalle,
            text="Detalle de señal",
            font=("Arial", 16, "bold")
        )

        titulo_detalle.pack(
            pady=(15, 10)
        )

        fila_detalle = tk.Frame(frame_detalle)
        fila_detalle.pack(fill="x", padx=20, pady=(0, 15))

        fila_detalle.columnconfigure(0, weight=2)
        fila_detalle.columnconfigure(1, weight=3)

        self.frame_estado_evidencia = tk.Frame(fila_detalle)
        self.frame_estado_evidencia.grid(
            row=0, column=0, sticky="nsew", padx=(0, 12)
        )

        frame_info_tablas = tk.Frame(fila_detalle)
        frame_info_tablas.grid(
            row=0, column=1, sticky="nsew", padx=(12, 0)
        )

        self.label_imagen_senal = tk.Label(
            self.frame_estado_evidencia,
            text="Sin evidencia disponible.",
        )
        self.label_imagen_senal.pack(pady=(10, 6))

        frame_estado = tk.Frame(self.frame_estado_evidencia)
        frame_estado.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(frame_estado, text="Estado:").pack(pady=(0, 5))

        self.combo_estado_senal = ttk.Combobox(
            frame_estado,
            values=("BUENO", "REGULAR", "MALO"),
            state="readonly",
            width=20,
        )
        self.combo_estado_senal.pack(pady=(0, 8))

        self.boton_actualizar_estado = tk.Button(
            frame_estado,
            text="Actualizar estado",
            command=self._actualizar_estado_senal,
            state="disabled",
            width=20,
        )
        self.boton_actualizar_estado.pack(pady=(0, 10))

        self.boton_eliminar_senal = tk.Button(
            frame_estado,
            text="Eliminar del inventario",
            command=self._eliminar_senal_seleccionada,
            state="disabled",
            width=20,
        )

        if self.usuario_autenticado.rol == RolUsuario.ADMINISTRADOR:
            self.boton_eliminar_senal.pack(pady=(0, 10))

        tk.Label(
            frame_info_tablas,
            text="Detecciones asociadas",
            font=("Arial", 12, "bold")
        ).pack(
            pady=(15, 5)
        )


        self.tabla_detecciones_senal = (
            ttk.Treeview(
                frame_info_tablas,
                columns=(
                    "fecha",
                    "confianza"
                ),
                show="headings",
                height=5
            )
        )

        self.tabla_detecciones_senal.heading(
            "fecha",
            text="Fecha"
        )

        self.tabla_detecciones_senal.heading(
            "confianza",
            text="Confianza"
        )

        self.detecciones_senal = {}
        self.tabla_detecciones_senal.bind(
            "<Double-1>", self._abrir_deteccion_desde_inventario
        )
        tk.Label(
            frame_info_tablas,
            text="Doble clic en una detección para ver su evidencia."
        ).pack()

        self.tabla_detecciones_senal.pack(
            fill="both",
            padx=20,
            pady=10
        )

        self.tabla_inventario = tabla

        self.tabla_inventario.bind(
            "<<TreeviewSelect>>",
            self._mostrar_detalle_senal
        )

        tk.Label(
            frame_info_tablas,
            text="Historial de estado",
            font=("Arial", 12, "bold")
        ).pack(
            pady=(10, 5)
        )


        self.tabla_historial_senal = ttk.Treeview(
            frame_info_tablas,
            columns=(
                "fecha",
                "cambio",
                "usuario",
                "comentario"
            ),
            show="headings",
            height=5
        )

        for columna in self.tabla_historial_senal["columns"]:
            self.tabla_historial_senal.column(
                columna,
                width=100,
                minwidth=40,
                stretch=True
            )

        for columna in self.tabla_detecciones_senal["columns"]:
            self.tabla_detecciones_senal.column(
                columna,
                width=100,
                minwidth=40,
                stretch=True
            )

        self.tabla_historial_senal.heading(
            "fecha",
            text="Fecha"
        )

        self.tabla_historial_senal.heading(
            "cambio",
            text="Cambio"
        )

        self.tabla_historial_senal.heading(
            "usuario",
            text="Usuario"
        )

        self.tabla_historial_senal.heading(
            "comentario",
            text="Comentario"
        )

        self.tabla_historial_senal.column(
            "fecha",
            width=140
        )

        self.tabla_historial_senal.column(
            "cambio",
            width=150
        )

        self.tabla_historial_senal.column(
            "usuario",
            width=100
        )

        self.tabla_historial_senal.column(
            "comentario",
            width=220
        )

        self.tabla_historial_senal.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        for senal in senales:

            fecha = (
                senal["fecha_actualizacion"]
                .replace("T", " ")
                [:19]
            )

            estado = (
                senal["estado_actual"]
                or "Sin estado"
            )

            tabla.insert(
                "",
                tk.END,
                iid=str(
                    senal["id"]
                ),
                values=(
                    senal[
                        "clase_nombre"
                    ],
                    f"{senal['latitud']:.6f}",
                    f"{senal['longitud']:.6f}",
                    estado,
                    fecha
                )
            )

        scrollbar = ttk.Scrollbar(
            frame_lista,
            orient="vertical",
            command=tabla.yview
        )

        tabla.configure(
            yscrollcommand=scrollbar.set
        )

        tabla.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.label_estado.config(
            text=(
                f"Señales en inventario: "
                f"{len(senales)}"
            )
        )

        if senal_id is not None:
            if tabla.exists(senal_id):
                tabla.selection_set(senal_id)
                tabla.focus(senal_id)
                tabla.see(senal_id)
            else:
                self.label_estado.config(text="La señal ya no está en el inventario.")

    def mostrar_mapa(self):

        self._limpiar_contenido_actual()
        self._marcar_vista_activa("mapa")

        self.titulo_contenido.config(
            text="Mapa"
        )

        self.texto_contenido.pack_forget()

        self.label_estado.config(
            text="Cargando señales..."
        )

        try:

            senales = (
                self.cliente_api
                .listar_senales()
            )

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            return

        self.contenido_actual = tk.Frame(
            self.frame_contenido
        )

        self.contenido_actual.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        raiz = Path(__file__).resolve().parents[2]
        ruta_mapa = raiz / "data/mapas/prueba_negrita.sqlite3"

        if not ruta_mapa.is_file():
            self.label_estado.config(
                text="No se encontró la base del mapa local."
            )
            return

        mapa = TkinterMapView(
            self.contenido_actual,
            width=900,
            height=650,
            corner_radius=0,
            database_path=str(ruta_mapa),
            use_database_only=True,
            max_zoom=16
        )

        mapa.pack(
            fill="both",
            expand=True
        )

        mapa.set_position(9.7, -84.2)
        mapa.set_zoom(7)

        tk.Label(
            self.contenido_actual,
            text="© OpenStreetMap contributors · Geofabrik · Límites: geoBoundaries"
        ).pack(fill="x")

        for senal in senales:

            mapa.set_marker(
                senal["latitud"],
                senal["longitud"],
                text=senal["clase_nombre"],
                command=lambda _, id_senal=str(senal["id"]): self.ventana.after_idle(
                    lambda: self.mostrar_inventario(senal_id=id_senal)
                )
            )

        self.mapa_widget = mapa

        self.label_estado.config(
            text=(
                f"Señales en mapa: "
                f"{len(senales)}"
            )
        )


    def mostrar_usuarios(self):
        self._limpiar_contenido_actual()
        self._marcar_vista_activa("usuarios")
        self.titulo_contenido.config(text="Gestión de usuarios")
        self.texto_contenido.pack_forget()
        self.label_estado.config(text="Consultando usuarios...")

        try:
            usuarios = self.cliente_api.listar_usuarios()
        except SesionExpiradaError:
            return
        except RuntimeError as error:
            self.label_estado.config(text=str(error))
            self._marcar_vista_activa()
            return

        self.contenido_actual = ttk.Frame(self.frame_contenido)
        self.contenido_actual.pack(fill="both", expand=True, padx=20, pady=10)

        frame_tabla = ttk.Frame(self.contenido_actual)
        frame_tabla.pack(fill="x")

        self.tabla_usuarios = ttk.Treeview(
            frame_tabla,
            columns=("usuario", "rol", "estado"),
            show="headings",
            selectmode="browse",
            height=20,
        )

        self.tabla_usuarios.heading("usuario", text="Usuario")
        self.tabla_usuarios.heading("rol", text="Rol")
        self.tabla_usuarios.heading("estado", text="Estado")

        self.tabla_usuarios.column("usuario", width=220)
        self.tabla_usuarios.column("rol", width=150, anchor="center")
        self.tabla_usuarios.column("estado", width=120, anchor="center")

        controles = ttk.Frame(self.contenido_actual)
        controles.pack(fill="x", pady=(16, 8), ipady=4)

        ttk.Label(controles, text="Rol:").pack(side="left")

        self.combo_rol_usuario = ttk.Combobox(
            controles,
            values=tuple(rol.value for rol in RolUsuario),
            state="disabled",
            width=18,
        )
        self.combo_rol_usuario.pack(side="left", padx=8)

        self.boton_cambiar_rol = ttk.Button(
            controles,
            text="Cambiar rol",
            command=self._cambiar_rol_usuario,
            state="disabled",
        )
        self.boton_cambiar_rol.pack(side="left", padx=4)

        self.boton_estado_usuario = ttk.Button(
            controles,
            text="Activar / Desactivar",
            command=self._alternar_estado_usuario,
            state="disabled",
        )
        self.boton_estado_usuario.pack(side="left", padx=4)

        self.boton_eliminar_usuario = ttk.Button(
            controles,
            text="Eliminar",
            command=self._eliminar_usuario_seleccionado,
            state="disabled",
        )
        self.boton_eliminar_usuario.pack(side="left", padx=4)

        ttk.Button(
            controles,
            text="Agregar usuario",
            command=self._abrir_formulario_usuario,
        ).pack(side="right")

        self.tabla_usuarios.bind(
            "<<TreeviewSelect>>",
            self._seleccionar_usuario,
        )

        scroll = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=self.tabla_usuarios.yview,
        )
        self.tabla_usuarios.configure(yscrollcommand=scroll.set)

        scroll.pack(side="right", fill="y")
        self.tabla_usuarios.pack(side="left", fill="both", expand=True)

        for usuario in usuarios:
            self.tabla_usuarios.insert(
                "",
                "end",
                iid=str(usuario["id"]),
                values=(
                    usuario["nombre_usuario"],
                    usuario["rol"],
                    "Activo" if usuario["activo"] else "Inactivo",
                ),
            )

        self.label_estado.config(text=f"Usuarios encontrados: {len(usuarios)}")

    def _abrir_formulario_usuario(self):
        dialogo = tk.Toplevel(self.ventana)
        dialogo.title("Agregar usuario")
        dialogo.transient(self.ventana)
        dialogo.resizable(False, False)

        formulario = ttk.Frame(dialogo, padding=16)
        formulario.pack(fill="both", expand=True)

        ttk.Label(formulario, text="Usuario").grid(row=0, column=0, sticky="w")
        entrada_usuario = ttk.Entry(formulario, width=28)
        entrada_usuario.grid(row=0, column=1, padx=(10, 0), pady=5)

        ttk.Label(formulario, text="Contraseña").grid(row=1, column=0, sticky="w")
        entrada_password = ttk.Entry(formulario, width=28, show="*")
        entrada_password.grid(row=1, column=1, padx=(10, 0), pady=5)

        ttk.Label(formulario, text="Rol").grid(row=2, column=0, sticky="w")
        combo_rol = ttk.Combobox(
            formulario,
            values=tuple(rol.value for rol in RolUsuario),
            state="readonly",
            width=25,
        )
        combo_rol.set(RolUsuario.CAMPO.value)
        combo_rol.grid(row=2, column=1, padx=(10, 0), pady=5)

        def guardar():
            nombre = entrada_usuario.get().strip()
            password = entrada_password.get()

            if not nombre or not password:
                messagebox.showwarning(
                    "Agregar usuario",
                    "Completá el nombre de usuario y la contraseña.",
                    parent=dialogo,
                )
                return

            try:
                usuario = self.cliente_api.crear_usuario(
                    nombre,
                    password,
                    combo_rol.get(),
                )
            except SesionExpiradaError:
                return
            except RuntimeError as error:
                messagebox.showerror("Agregar usuario", str(error), parent=dialogo)
                return

            dialogo.destroy()
            self.mostrar_usuarios()

        botones = ttk.Frame(formulario)
        botones.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))

        ttk.Button(botones, text="Cancelar", command=dialogo.destroy).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(botones, text="Guardar", command=guardar).pack(side="left")

        dialogo.wait_visibility()
        dialogo.grab_set()
        entrada_usuario.focus_set()

    def _seleccionar_usuario(self, event=None):
        seleccion = self.tabla_usuarios.selection()
        usuario_id = seleccion[0] if seleccion else None
        puede_editar = (
            usuario_id is not None
            and usuario_id != str(self.usuario_autenticado.id)
        )

        self.combo_rol_usuario.configure(
            state="readonly" if puede_editar else "disabled"
        )
        estado_boton = "normal" if puede_editar else "disabled"
        self.boton_cambiar_rol.configure(state=estado_boton)
        self.boton_estado_usuario.configure(state=estado_boton)
        self.boton_eliminar_usuario.configure(state=estado_boton)

        if usuario_id is None:
            self.combo_rol_usuario.set("")
            self.boton_estado_usuario.configure(text="Activar / Desactivar")
            return

        _, rol, estado = self.tabla_usuarios.item(usuario_id, "values")
        self.combo_rol_usuario.set(rol)
        self.boton_estado_usuario.configure(
            text="Desactivar" if estado == "Activo" else "Activar"
        )


    def _cambiar_rol_usuario(self):
        seleccion = self.tabla_usuarios.selection()
        if seleccion:
            self._guardar_cambios_usuario(
                seleccion[0],
                {"rol": self.combo_rol_usuario.get()},
            )


    def _alternar_estado_usuario(self):
        seleccion = self.tabla_usuarios.selection()
        if not seleccion:
            return

        usuario_id = seleccion[0]
        nombre, _, estado = self.tabla_usuarios.item(usuario_id, "values")
        activar = estado != "Activo"

        if not activar and not messagebox.askyesno(
            "Desactivar usuario",
            f"¿Querés desactivar la cuenta de {nombre}?",
            parent=self.ventana,
        ):
            return

        self._guardar_cambios_usuario(usuario_id, {"activo": activar})

    def _eliminar_usuario_seleccionado(self):
        seleccion = self.tabla_usuarios.selection()
        if not seleccion:
            return

        usuario_id = seleccion[0]
        nombre = self.tabla_usuarios.set(usuario_id, "usuario")

        if not messagebox.askyesno(
            "Eliminar usuario",
            f"¿Querés eliminar definitivamente la cuenta de {nombre}?",
            parent=self.ventana,
        ):
            return

        try:
            self.cliente_api.eliminar_usuario(usuario_id)
        except SesionExpiradaError:
            return
        except RuntimeError as error:
            messagebox.showerror("Eliminar usuario", str(error), parent=self.ventana)
            return

        self.tabla_usuarios.delete(usuario_id)
        self._seleccionar_usuario()
        self.label_estado.config(text=f"Cuenta eliminada: {nombre}.")

    def _guardar_cambios_usuario(self, usuario_id, cambios):
        try:
            usuario = self.cliente_api.actualizar_usuario(usuario_id, cambios)
        except SesionExpiradaError:
            return
        except RuntimeError as error:
            messagebox.showerror("Gestión de usuarios", str(error), parent=self.ventana)
            return

        self.tabla_usuarios.item(
            usuario_id,
            values=(
                usuario["nombre_usuario"],
                usuario["rol"],
                "Activo" if usuario["activo"] else "Inactivo",
            ),
        )
        self._seleccionar_usuario()
        self.label_estado.config(
            text=f"Cuenta actualizada: {usuario['nombre_usuario']}."
        )


    def mostrar_modelos(self):

        self._limpiar_contenido_actual()
        self._marcar_vista_activa("modelos")
        self.titulo_contenido.config(
            text="Gestión de modelos"
        )

        self.texto_contenido.pack_forget()

        self.contenido_actual = GestionModelos(
            self.frame_contenido,
            cliente_api=self.cliente_api,
            callback_estado=lambda mensaje: (
                self.label_estado.config(
                    text=mensaje
                )
            )
        )

        self.contenido_actual.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )


    def mostrar_dataset(self):

        self._limpiar_contenido_actual()
        self._marcar_vista_activa("dataset")

        self.titulo_contenido.config(
            text="Etiquetado de dataset"
        )

        self.texto_contenido.pack_forget()

        self.contenido_actual = EtiquetadorDataset(
            self.frame_contenido,
            cliente_api=self.cliente_api,
            callback_estado=lambda mensaje: (
                self.label_estado.config(
                    text=mensaje
                )
            )
        )

        self.contenido_actual.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

    def _limpiar_contenido_actual(self):

        if self.contenido_actual is not None:
            self.contenido_actual.destroy()
            self.contenido_actual = None

    def cerrar_sesion_expirada(self):
        self.sesion_expirada = True

        messagebox.showwarning(
            "Sesión expirada",
            "Tu sesión ha expirado. Debes iniciar sesión nuevamente."
        )

        self.ventana.destroy()


    def ejecutar(self):

        self.ventana.wait_window()

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
                self.label_estado.config(
                    text=(
                        "Sesión renovada "
                        "por actividad."
                    )
                )

        except SesionExpiradaError:
            return

        except RuntimeError as error:
            self.label_estado.config(
                text=str(error)
            )

        self._programar_verificacion_sesion()

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

        self.ventana.destroy()

    def _aprobar_deteccion(self):

        deteccion_id = (
            self.deteccion_seleccionada_id
        )

        if deteccion_id is None:
            return

        confirmar = messagebox.askyesno(
            "Aprobar detección",
            (
                "¿Confirma que desea aprobar "
                "esta detección?"
            )
        )

        if not confirmar:
            return

        self._revisar_deteccion(
            resultado="APPROVED"
        )

    def _rechazar_deteccion(self):

        deteccion_id = (
            self.deteccion_seleccionada_id
        )

        if deteccion_id is None:
            return

        comentario = simpledialog.askstring(
            "Rechazar detección",
            (
                "Ingrese el motivo del rechazo "
                "(opcional):"
            ),
            parent=self.ventana
        )

        if comentario is None:
            return

        comentario = comentario.strip()

        if not comentario:
            comentario = None

        self._revisar_deteccion(
            resultado="REJECTED",
            comentario=comentario
        )

    def _revisar_deteccion(
        self,
        resultado: str,
        comentario: str | None = None
    ):

        deteccion_id = (
            self.deteccion_seleccionada_id
        )

        if deteccion_id is None:
            return

        self.boton_aprobar.config(
            state="disabled"
        )

        self.boton_rechazar.config(
            state="disabled"
        )

        self.label_estado.config(
            text="Guardando revisión..."
        )

        try:

            self.cliente_api.revisar_deteccion(
                deteccion_id=deteccion_id,
                resultado=resultado,
                comentario=comentario
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            self.boton_aprobar.config(
                state="normal"
            )

            self.boton_rechazar.config(
                state="normal"
            )

            return

        self.deteccion_seleccionada_id = None

        if resultado == "APPROVED":

            self.label_estado.config(
                text="Detección aprobada."
            )

        else:

            self.label_estado.config(
                text="Detección rechazada."
            )

        self.mostrar_detecciones()

    def _mostrar_detalle_senal(
        self,
        event=None
    ):

        seleccion = (
            self.tabla_inventario
            .selection()
        )

        if not seleccion:
            self.boton_eliminar_senal.config(state="disabled")
            return

        senal_id = seleccion[0]

        self.senal_seleccionada_id = senal_id

        senal = (
            self.senales_inventario
            .get(
                senal_id
            )
        )

        if senal is None:
            return

        self.detecciones_senal = {}
        filas = self.tabla_detecciones_senal.get_children()
        if filas:
            self.tabla_detecciones_senal.delete(*filas)
        self.label_imagen_senal.unbind("<Button-1>")
        self.label_imagen_senal.config(image="", text="Sin evidencia disponible.", cursor="")
        self.label_imagen_senal.image = None
        self.imagen_senal_tk = None

        estado_actual = (
            senal["estado_actual"]
        )

        if estado_actual is not None:

            self.combo_estado_senal.set(
                estado_actual
            )

        else:

            self.combo_estado_senal.set(
                ""
            )

        self.boton_actualizar_estado.config(
            state="normal"
        )

        self.boton_eliminar_senal.config(state="normal")

        estado = (
            senal["estado_actual"]
            or "Sin estado"
        )

        texto = (
            f"Clase: "
            f"{senal['clase_nombre']}\n\n"

            f"Latitud: "
            f"{senal['latitud']:.6f}\n\n"

            f"Longitud: "
            f"{senal['longitud']:.6f}\n\n"

            f"Estado: "
            f"{estado}"
        )

        try:

            detecciones = (
                self.cliente_api
                .listar_detecciones(
                    senal_id=senal_id
                )
            )

            self.label_imagen_senal.config(
                image="",
                text="Sin evidencia disponible."
            )

            self.imagen_senal_tk = None

            if detecciones:

                deteccion = detecciones[0]

                try:

                    imagen = self._cargar_imagen_deteccion(deteccion)

                    ancho_columna = self.frame_estado_evidencia.winfo_width()
                    ancho_foto = min(450, max(1, ancho_columna - 20))

                    imagen.thumbnail(
                        (ancho_foto, 300),
                        Image.Resampling.LANCZOS,
                    )

                    self.imagen_senal_tk = (
                        ImageTk.PhotoImage(
                            imagen
                        )
                    )

                    self.label_imagen_senal.config(
                        image=self.imagen_senal_tk,
                        text=""
                    )

                    self.label_imagen_senal.image = (
                        self.imagen_senal_tk
                    )

                    self.label_imagen_senal.config(cursor="hand2")
                    self.label_imagen_senal.bind(
                        "<Button-1>",
                        lambda _, actual=deteccion: self._abrir_evidencia_inventario(actual)
                    )

                except (RuntimeError, OSError):
                    self.label_imagen_senal.config(
                        text="No se pudo cargar la evidencia."
                    )

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            return

        self.detecciones_senal = {
            str(deteccion["id"]): deteccion for deteccion in detecciones
        }

        for deteccion in detecciones:

            fecha = (
                deteccion["fecha_hora"]
                .replace("T", " ")
                [:19]
            )

            confianza = (
                f"{deteccion['confianza'] * 100:.1f}%"
            )

            self.tabla_detecciones_senal.insert(
                "",
                tk.END,
                iid=str(
                    deteccion["id"]
                ),
                values=(
                    fecha,
                    confianza
                )
            )

        self.label_estado.config(
            text=(
                f"Detecciones asociadas: "
                f"{len(detecciones)}"
            )
        )

        self._cargar_historial_senal(
            senal_id
        )

    def _cargar_imagen_deteccion(self, deteccion):
        evidencia = self.cliente_api.obtener_evidencia_deteccion(str(deteccion["id"]))
        with Image.open(BytesIO(evidencia)) as archivo:
            imagen = archivo.convert("RGB")

        ImageDraw.Draw(imagen).rectangle(
            (deteccion["bbox_x1"], deteccion["bbox_y1"],
             deteccion["bbox_x2"], deteccion["bbox_y2"]),
            outline="red", width=max(2, imagen.width // 300)
        )
        return imagen

    def _abrir_deteccion_desde_inventario(self, event):
        fila = self.tabla_detecciones_senal.identify_row(event.y)
        deteccion = self.detecciones_senal.get(fila)
        if deteccion is not None:
            self._abrir_evidencia_inventario(deteccion)

    def _abrir_evidencia_inventario(self, deteccion):
        try:
            imagen = self._cargar_imagen_deteccion(deteccion)
        except SesionExpiradaError:
            return
        except (RuntimeError, OSError) as error:
            messagebox.showerror("Evidencia", str(error), parent=self.ventana)
            return

        ventana = tk.Toplevel(self.ventana)
        ventana.title("Detalle de evidencia")
        imagen.thumbnail(
            (max(100, min(900, ventana.winfo_screenwidth() - 100)),
             max(100, min(650, ventana.winfo_screenheight() - 220))),
            Image.Resampling.LANCZOS
        )
        foto = ImageTk.PhotoImage(imagen, master=ventana)
        vista = tk.Label(ventana, image=foto)
        vista.image = foto
        vista.pack(padx=12, pady=12)

        fecha = deteccion["fecha_hora"].replace("T", " ")[:19]
        datos = [
            f"Clase: {deteccion['clase_nombre']}",
            f"Confianza: {deteccion['confianza'] * 100:.1f} %",
            f"Fecha: {fecha}",
            f"Revisión: {deteccion['estado_revision']}"
        ]
        latitud = deteccion.get("latitud_captura")
        longitud = deteccion.get("longitud_captura")
        if latitud is not None and longitud is not None:
            datos.append(f"Ubicación de captura: {latitud:.6f}, {longitud:.6f}")
        precision = deteccion.get("precision_ubicacion_m")
        if precision is not None:
            datos.append(f"Precisión de ubicación: {precision:.1f} m")

        tk.Label(ventana, text="\n".join(datos), justify="left").pack(
            anchor="w", padx=12, pady=(0, 12)
        )

    def _cargar_historial_senal(
        self,
        senal_id: str
    ):

        try:

            historial = (
                self.cliente_api
                .obtener_historial_senal(
                    senal_id
                )
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            return

        for item in (
            self.tabla_historial_senal
            .get_children()
        ):

            self.tabla_historial_senal.delete(
                item
            )

        for cambio in historial:

            fecha = (
                cambio["fecha_cambio"]
                .replace("T", " ")
                [:19]
            )

            anterior = (
                cambio["estado_anterior"]
                or "Sin evaluar"
            )

            nuevo = (
                cambio["estado_nuevo"]
            )

            comentario = (
                cambio["comentario"]
                or ""
            )

            self.tabla_historial_senal.insert(
                "",
                tk.END,
                values=(
                    fecha,
                    f"{anterior} → {nuevo}",
                    cambio["nombre_usuario"],
                    comentario
                )
            )

    def _actualizar_estado_senal(
        self
    ):

        senal_id = (
            self.senal_seleccionada_id
        )

        if senal_id is None:
            return

        estado_nuevo = (
            self.combo_estado_senal
            .get()
            .strip()
        )

        if not estado_nuevo:

            messagebox.showwarning(
                "Estado requerido",
                "Seleccione un estado."
            )

            return

        senal = (
            self.senales_inventario
            .get(
                senal_id
            )
        )

        if senal is None:
            return

        if (
            senal["estado_actual"]
            == estado_nuevo
        ):

            messagebox.showinfo(
                "Sin cambios",
                (
                    "La señal ya tiene "
                    f"el estado {estado_nuevo}."
                )
            )

            return

        comentario = simpledialog.askstring(
            "Actualizar estado",
            (
                "Comentario sobre el "
                "cambio (opcional):"
            ),
            parent=self.ventana
        )

        if comentario is None:
            return

        comentario = comentario.strip()

        if not comentario:
            comentario = None

        confirmar = messagebox.askyesno(
            "Actualizar estado",
            (
                "¿Desea cambiar el estado "
                f"de la señal a {estado_nuevo}?"
            )
        )

        if not confirmar:
            return

        self.boton_actualizar_estado.config(
            state="disabled"
        )

        self.label_estado.config(
            text="Actualizando estado..."
        )

        try:

            senal_actualizada = (
                self.cliente_api
                .actualizar_estado_senal(
                    senal_id=senal_id,
                    estado=estado_nuevo,
                    comentario=comentario
                )
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:

            self.label_estado.config(
                text=str(error)
            )

            self.boton_actualizar_estado.config(
                state="normal"
            )

            return

        self.senales_inventario[
            senal_id
        ] = senal_actualizada

        valores = list(
            self.tabla_inventario.item(
                senal_id,
                "values"
            )
        )

        valores[3] = (
            senal_actualizada[
                "estado_actual"
            ]
        )

        fecha = (
            senal_actualizada[
                "fecha_actualizacion"
            ]
            .replace("T", " ")
            [:19]
        )

        valores[4] = fecha

        self.tabla_inventario.item(
            senal_id,
            values=valores
        )

        self.label_detalle_senal.config(
            text=(
                f"Clase: "
                f"{senal_actualizada['clase_nombre']}\n\n"

                f"Latitud: "
                f"{senal_actualizada['latitud']:.6f}\n\n"

                f"Longitud: "
                f"{senal_actualizada['longitud']:.6f}\n\n"

                f"Estado: "
                f"{senal_actualizada['estado_actual']}"
            )
        )

        self._cargar_historial_senal(
            senal_id
        )

        self.boton_actualizar_estado.config(
            state="normal"
        )

        self.label_estado.config(
            text=(
                "Estado actualizado a "
                f"{estado_nuevo}."
            )
        )

    def _eliminar_senal_seleccionada(self):
        seleccion = self.tabla_inventario.selection()
        if not seleccion:
            return

        senal_id = seleccion[0]
        senal = self.senales_inventario.get(senal_id)
        if senal is None:
            return

        if not messagebox.askyesno(
            "Eliminar del inventario",
            f"¿Querés retirar la señal «{senal['clase_nombre']}» del inventario "
            "y del mapa? Se conservarán sus detecciones y su historial.",
            parent=self.ventana,
        ):
            return

        try:
            self.cliente_api.eliminar_senal(senal_id)
        except SesionExpiradaError:
            return
        except RuntimeError as error:
            messagebox.showerror(
                "Eliminar del inventario",
                str(error),
                parent=self.ventana,
            )
            return

        self.senal_seleccionada_id = None
        self.mostrar_inventario()

    def _marcar_vista_activa(self, vista=None):
        for nombre, boton in self.botones_vistas.items():
            boton.configure(
                state=tk.DISABLED if nombre == vista else tk.NORMAL
            )