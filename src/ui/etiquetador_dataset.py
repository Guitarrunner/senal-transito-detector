import tkinter as tk
from io import BytesIO
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from src.gestion.cliente_api import ClienteGestion


class EtiquetadorDataset(tk.Frame):

    ANCHO_CANVAS = 700
    ALTO_CANVAS = 520

    def __init__(
        self,
        parent,
        cliente_api: ClienteGestion,
        callback_estado=None
    ):
        super().__init__(parent)

        self.cliente_api = cliente_api
        self.callback_estado = callback_estado

        self.datasets = []
        self.imagenes = []
        self.clases = []
        self.anotaciones = []

        self.imagen_actual = None
        self.imagen_original = None
        self.imagen_tk = None

        self.escala = 1.0
        self.escala_ajuste = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.inicio_x = None
        self.inicio_y = None

        self.rectangulo_temporal = None
        self.bbox_pendiente = None

        self._crear_componentes()
        self._cargar_datos_iniciales()

    def _crear_componentes(self):

        # ===== SELECCIÓN DE DATASET =====

        frame_superior = tk.Frame(self)

        frame_superior.pack(
            fill="x",
            pady=(0, 10)
        )

        tk.Label(
            frame_superior,
            text="Dataset:",
            font=("Arial", 11, "bold")
        ).pack(
            side="left",
            padx=(0, 5)
        )

        self.combo_dataset = ttk.Combobox(
            frame_superior,
            state="readonly",
            width=40
        )

        self.combo_dataset.pack(
            side="left",
            padx=5
        )

        self.combo_dataset.bind(
            "<<ComboboxSelected>>",
            self._dataset_seleccionado
        )

        tk.Button(
            frame_superior,
            text="Actualizar",
            command=self._cargar_datos_iniciales
        ).pack(
            side="left",
            padx=5
        )

        # ===== CONTENIDO =====

        cuerpo = tk.Frame(self)

        cuerpo.pack(
            fill="both",
            expand=True
        )

        # ----- imágenes -----

        frame_imagenes = tk.Frame(
            cuerpo,
            width=200
        )

        frame_imagenes.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )

        tk.Label(
            frame_imagenes,
            text="Imágenes",
            font=("Arial", 11, "bold")
        ).pack(
            pady=(0, 5)
        )

        tk.Button(
            frame_imagenes,
            text="Cargar imágenes",
            command=self._cargar_imagenes_bulk
        ).pack(
            fill="x",
            pady=(0, 10)
        )

        self.lista_imagenes = tk.Listbox(
            frame_imagenes,
            width=27,
            height=28
        )

        self.lista_imagenes.pack(
            fill="y",
            expand=True
        )

        self.lista_imagenes.bind(
            "<<ListboxSelect>>",
            self._imagen_seleccionada
        )

        # ----- canvas -----

        frame_canvas = tk.Frame(cuerpo)

        frame_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        frame_zoom = tk.Frame(
            frame_canvas
        )

        frame_zoom.pack(
            fill="x",
            pady=(0, 5)
        )

        tk.Button(
            frame_zoom,
            text="-",
            width=3,
            command=lambda: self._cambiar_zoom(0.8)
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            frame_zoom,
            text="Ajustar",
            command=self._ajustar_zoom
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            frame_zoom,
            text="100%",
            command=self._zoom_100
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            frame_zoom,
            text="+",
            width=3,
            command=lambda: self._cambiar_zoom(1.25)
        ).pack(
            side="left",
            padx=2
        )

        self.label_zoom = tk.Label(
            frame_zoom,
            text=""
        )

        self.label_zoom.pack(
            side="left",
            padx=10
        )


        contenedor_canvas = tk.Frame(
            frame_canvas
        )

        contenedor_canvas.pack(
            fill="both",
            expand=True
        )


        self.canvas = tk.Canvas(
            contenedor_canvas,
            width=self.ANCHO_CANVAS,
            height=self.ALTO_CANVAS,
            bg="#303030",
            cursor="cross"
        )

        scroll_vertical = ttk.Scrollbar(
            contenedor_canvas,
            orient="vertical",
            command=self.canvas.yview
        )

        scroll_horizontal = ttk.Scrollbar(
            contenedor_canvas,
            orient="horizontal",
            command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=scroll_vertical.set,
            xscrollcommand=scroll_horizontal.set
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scroll_vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scroll_horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        contenedor_canvas.grid_rowconfigure(
            0,
            weight=1
        )

        contenedor_canvas.grid_columnconfigure(
            0,
            weight=1
        )

        self.canvas.bind(
            "<ButtonPress-1>",
            self._iniciar_bbox
        )

        self.canvas.bind(
            "<B1-Motion>",
            self._dibujar_bbox
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self._finalizar_bbox
        )

        self.canvas.bind(
            "<MouseWheel>",
            self._scroll_vertical
        )

        self.canvas.bind(
            "<Shift-MouseWheel>",
            self._scroll_horizontal
        )

        self.label_bbox = tk.Label(
            frame_canvas,
            text="Dibuje un bounding box sobre la imagen."
        )

        self.label_bbox.pack(
            pady=5
        )

        # ----- controles -----

        frame_controles = tk.Frame(
            cuerpo,
            width=230
        )

        frame_controles.pack(
            side="right",
            fill="y",
            padx=(10, 0)
        )

        tk.Label(
            frame_controles,
            text="Clase",
            font=("Arial", 11, "bold")
        ).pack(
            pady=(0, 5)
        )

        self.combo_clase = ttk.Combobox(
            frame_controles,
            state="readonly",
            width=27
        )

        self.combo_clase.pack(
            pady=(0, 10)
        )

        self.boton_guardar = tk.Button(
            frame_controles,
            text="Guardar anotación",
            command=self._guardar_anotacion,
            width=24
        )

        self.boton_guardar.pack(
            pady=5
        )

        tk.Label(
            frame_controles,
            text="Anotaciones",
            font=("Arial", 11, "bold")
        ).pack(
            pady=(20, 5)
        )

        self.lista_anotaciones = tk.Listbox(
            frame_controles,
            width=32,
            height=15
        )

        self.lista_anotaciones.pack()

        tk.Button(
            frame_controles,
            text="Eliminar anotación",
            command=self._eliminar_anotacion,
            width=24
        ).pack(
            pady=10
        )

    # ======================================================
    # DATOS
    # ======================================================

    def _cargar_datos_iniciales(self):

        try:
            self.datasets = (
                self.cliente_api.listar_datasets()
            )

            self.clases = (
                self.cliente_api.listar_clases()
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        valores_dataset = []

        for dataset in self.datasets:
            valores_dataset.append(
                (
                    f"{dataset['nombre']} "
                    f"({dataset['id'][:8]})"
                )
            )

        self.combo_dataset["values"] = (
            valores_dataset
        )

        valores_clases = []

        for clase in self.clases:
            valores_clases.append(
                (
                    f"{clase['codigo']} - "
                    f"{clase['nombre']}"
                )
            )

        self.combo_clase["values"] = (
            valores_clases
        )

        if self.clases:
            self.combo_clase.current(0)

        if self.datasets:
            self.combo_dataset.current(0)
            self._cargar_imagenes_dataset(0)

        self._estado(
            "Datos del etiquetador cargados."
        )

    def _dataset_seleccionado(self, event=None):

        indice = self.combo_dataset.current()

        if indice < 0:
            return

        self._cargar_imagenes_dataset(
            indice
        )

    def _cargar_imagenes_dataset(
        self,
        indice_dataset
    ):

        dataset = self.datasets[
            indice_dataset
        ]

        try:
            self.imagenes = (
                self.cliente_api.listar_imagenes(
                    dataset["id"]
                )
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        self.lista_imagenes.delete(
            0,
            tk.END
        )

        for imagen in self.imagenes:
            self.lista_imagenes.insert(
                tk.END,
                imagen["nombre_archivo"]
            )

        self._limpiar_canvas()

        self._estado(
            (
                f"{len(self.imagenes)} imágenes "
                f"en el dataset."
            )
        )

    def _imagen_seleccionada(
        self,
        event=None
    ):

        seleccion = (
            self.lista_imagenes.curselection()
        )

        if not seleccion:
            return

        indice = seleccion[0]

        self.imagen_actual = (
            self.imagenes[indice]
        )

        try:
            contenido = (
                self.cliente_api.obtener_imagen(
                    self.imagen_actual["id"]
                )
            )

            self.anotaciones = (
                self.cliente_api.listar_anotaciones(
                    self.imagen_actual["id"]
                )
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        self.imagen_original = (
            Image.open(
                BytesIO(contenido)
            ).convert("RGB")
        )

        self._ajustar_zoom()

        self._estado(
            self.imagen_actual[
                "nombre_archivo"
            ]
        )

    # ======================================================
    # IMAGEN
    # ======================================================

    def _mostrar_imagen(self):

        self.canvas.delete("all")

        if self.imagen_original is None:
            return

        ancho_original, alto_original = (
            self.imagen_original.size
        )

        ancho_mostrado = max(
            1,
            round(
                ancho_original
                * self.escala
            )
        )

        alto_mostrado = max(
            1,
            round(
                alto_original
                * self.escala
            )
        )

        imagen_redimensionada = (
            self.imagen_original.resize(
                (
                    ancho_mostrado,
                    alto_mostrado
                ),
                Image.Resampling.LANCZOS
            )
        )

        self.imagen_tk = ImageTk.PhotoImage(
            imagen_redimensionada
        )

        self.offset_x = max(
            (
                self.ANCHO_CANVAS
                - ancho_mostrado
            ) // 2,
            0
        )

        self.offset_y = max(
            (
                self.ALTO_CANVAS
                - alto_mostrado
            ) // 2,
            0
        )

        self.canvas.create_image(
            self.offset_x,
            self.offset_y,
            anchor="nw",
            image=self.imagen_tk
        )

        ancho_scroll = max(
            self.ANCHO_CANVAS,
            self.offset_x
            + ancho_mostrado
        )

        alto_scroll = max(
            self.ALTO_CANVAS,
            self.offset_y
            + alto_mostrado
        )

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                ancho_scroll,
                alto_scroll
            )
        )

        self.label_zoom.config(
            text=(
                f"{self.escala * 100:.0f}%"
            )
        )

        self._dibujar_anotaciones_existentes()

    def _dibujar_anotaciones_existentes(
        self
    ):

        self.lista_anotaciones.delete(
            0,
            tk.END
        )

        for anotacion in self.anotaciones:

            x1 = (
                self.offset_x
                + anotacion["bbox_x1"]
                * self.escala
            )

            y1 = (
                self.offset_y
                + anotacion["bbox_y1"]
                * self.escala
            )

            x2 = (
                self.offset_x
                + anotacion["bbox_x2"]
                * self.escala
            )

            y2 = (
                self.offset_y
                + anotacion["bbox_y2"]
                * self.escala
            )

            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline="red",
                width=2
            )

            self.canvas.create_text(
                x1 + 4,
                y1 + 4,
                text=anotacion[
                    "clase_nombre"
                ],
                anchor="nw",
                fill="red",
                font=("Arial", 10, "bold")
            )

            self.lista_anotaciones.insert(
                tk.END,
                (
                    f"{anotacion['clase_nombre']} "
                    f"({anotacion['bbox_x1']},"
                    f"{anotacion['bbox_y1']}) "
                    f"- "
                    f"({anotacion['bbox_x2']},"
                    f"{anotacion['bbox_y2']})"
                )
            )

    # ======================================================
    # DIBUJAR BOUNDING BOX
    # ======================================================

    def _coordenada_en_imagen(
        self,
        x,
        y
    ):
        if self.imagen_original is None:
            return None

        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)
        
        ancho, alto = (
            self.imagen_original.size
        )

        x_min = self.offset_x
        y_min = self.offset_y

        x_max = (
            self.offset_x
            + ancho * self.escala
        )

        y_max = (
            self.offset_y
            + alto * self.escala
        )

        x = max(
            x_min,
            min(x, x_max)
        )

        y = max(
            y_min,
            min(y, y_max)
        )

        return x, y

    def _iniciar_bbox(
        self,
        event
    ):

        if self.imagen_original is None:
            return

        coordenada = (
            self._coordenada_en_imagen(
                event.x,
                event.y
            )
        )

        if coordenada is None:
            return

        self.inicio_x, self.inicio_y = (
            coordenada
        )

        if self.rectangulo_temporal:
            self.canvas.delete(
                self.rectangulo_temporal
            )

        self.rectangulo_temporal = (
            self.canvas.create_rectangle(
                self.inicio_x,
                self.inicio_y,
                self.inicio_x,
                self.inicio_y,
                outline="yellow",
                width=2
            )
        )

    def _dibujar_bbox(
        self,
        event
    ):

        if (
            self.rectangulo_temporal
            is None
        ):
            return

        coordenada = (
            self._coordenada_en_imagen(
                event.x,
                event.y
            )
        )

        if coordenada is None:
            return

        x, y = coordenada

        self.canvas.coords(
            self.rectangulo_temporal,
            self.inicio_x,
            self.inicio_y,
            x,
            y
        )

    def _finalizar_bbox(
        self,
        event
    ):

        if (
            self.imagen_original is None
            or self.inicio_x is None
        ):
            return

        coordenada = (
            self._coordenada_en_imagen(
                event.x,
                event.y
            )
        )

        if coordenada is None:
            return

        fin_x, fin_y = coordenada

        canvas_x1 = min(
            self.inicio_x,
            fin_x
        )

        canvas_y1 = min(
            self.inicio_y,
            fin_y
        )

        canvas_x2 = max(
            self.inicio_x,
            fin_x
        )

        canvas_y2 = max(
            self.inicio_y,
            fin_y
        )

        x1 = round(
            (
                canvas_x1
                - self.offset_x
            )
            / self.escala
        )

        y1 = round(
            (
                canvas_y1
                - self.offset_y
            )
            / self.escala
        )

        x2 = round(
            (
                canvas_x2
                - self.offset_x
            )
            / self.escala
        )

        y2 = round(
            (
                canvas_y2
                - self.offset_y
            )
            / self.escala
        )

        ancho, alto = (
            self.imagen_original.size
        )

        x1 = max(
            0,
            min(x1, ancho)
        )

        y1 = max(
            0,
            min(y1, alto)
        )

        x2 = max(
            0,
            min(x2, ancho)
        )

        y2 = max(
            0,
            min(y2, alto)
        )

        if (
            x2 <= x1
            or y2 <= y1
        ):
            self.bbox_pendiente = None
            return

        self.bbox_pendiente = (
            x1,
            y1,
            x2,
            y2
        )

        self.label_bbox.config(
            text=(
                f"BBox: "
                f"({x1}, {y1}) → "
                f"({x2}, {y2})"
            )
        )

        self.inicio_x = None
        self.inicio_y = None

    # ======================================================
    # ANOTACIONES
    # ======================================================

    def _guardar_anotacion(self):

        if self.imagen_actual is None:
            messagebox.showwarning(
                "Sin imagen",
                "Seleccione una imagen."
            )
            return

        if self.bbox_pendiente is None:
            messagebox.showwarning(
                "Sin bounding box",
                "Dibuje un bounding box primero."
            )
            return

        indice_clase = (
            self.combo_clase.current()
        )

        if indice_clase < 0:
            messagebox.showwarning(
                "Sin clase",
                "Seleccione una clase."
            )
            return

        clase = self.clases[
            indice_clase
        ]

        x1, y1, x2, y2 = (
            self.bbox_pendiente
        )

        try:
            self.cliente_api.crear_anotacion(
                imagen_id=self.imagen_actual[
                    "id"
                ],
                clase_senal_id=clase["id"],
                bbox_x1=x1,
                bbox_y1=y1,
                bbox_x2=x2,
                bbox_y2=y2
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        self.bbox_pendiente = None
        self.rectangulo_temporal = None

        self.label_bbox.config(
            text="Anotación guardada."
        )

        self._recargar_anotaciones()

    def _recargar_anotaciones(self):

        if self.imagen_actual is None:
            return

        try:
            self.anotaciones = (
                self.cliente_api.listar_anotaciones(
                    self.imagen_actual["id"]
                )
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        self._mostrar_imagen()

    def _eliminar_anotacion(self):

        seleccion = (
            self.lista_anotaciones.curselection()
        )

        if not seleccion:
            messagebox.showwarning(
                "Sin selección",
                "Seleccione una anotación."
            )
            return

        indice = seleccion[0]

        anotacion = self.anotaciones[
            indice
        ]

        confirmar = messagebox.askyesno(
            "Eliminar anotación",
            (
                "¿Desea eliminar la anotación "
                f"{anotacion['clase_nombre']}?"
            )
        )

        if not confirmar:
            return

        try:
            self.cliente_api.eliminar_anotacion(
                imagen_id=self.imagen_actual[
                    "id"
                ],
                anotacion_id=anotacion["id"]
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        self._recargar_anotaciones()

    # ======================================================

    def _limpiar_canvas(self):

        self.canvas.delete("all")

        self.imagen_actual = None
        self.imagen_original = None
        self.imagen_tk = None

        self.anotaciones = []
        self.bbox_pendiente = None

        self.lista_anotaciones.delete(
            0,
            tk.END
        )

    def _estado(
        self,
        mensaje
    ):
        if self.callback_estado:
            self.callback_estado(
                mensaje
            )

    def _cargar_imagenes_bulk(self):

        indice_dataset = (
            self.combo_dataset.current()
        )

        if indice_dataset < 0:
            messagebox.showwarning(
                "Sin dataset",
                "Seleccione un dataset."
            )
            return

        rutas = filedialog.askopenfilenames(
            title="Seleccionar imágenes",
            filetypes=[
                (
                    "Imágenes",
                    "*.jpg *.jpeg *.png *.bmp *.heic *.heif"
                ),
                (
                    "Todos los archivos",
                    "*.*"
                )
            ]
        )

        if not rutas:
            return

        dataset = self.datasets[
            indice_dataset
        ]

        self._estado(
            f"Cargando {len(rutas)} imágenes..."
        )

        try:
            resultado = (
                self.cliente_api
                .subir_imagenes_bulk(
                    dataset["id"],
                    rutas
                )
            )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        cantidad_cargadas = len(
            resultado["cargadas"]
        )

        cantidad_errores = len(
            resultado["errores"]
        )

        mensaje = (
            f"{cantidad_cargadas} imágenes cargadas."
        )

        if cantidad_errores:
            mensaje += (
                f"\n{cantidad_errores} "
                f"no pudieron cargarse."
            )

        messagebox.showinfo(
            "Carga finalizada",
            mensaje
        )

        self._cargar_imagenes_dataset(
            indice_dataset
        )

    def _ajustar_zoom(self):

        if self.imagen_original is None:
            return

        ancho, alto = (
            self.imagen_original.size
        )

        escala_x = (
            self.ANCHO_CANVAS
            / ancho
        )

        escala_y = (
            self.ALTO_CANVAS
            / alto
        )

        self.escala_ajuste = min(
            escala_x,
            escala_y,
            1.0
        )

        self.escala = (
            self.escala_ajuste
        )

        self._mostrar_imagen()


    def _zoom_100(self):

        if self.imagen_original is None:
            return

        self.escala = 1.0

        self._mostrar_imagen()


    def _cambiar_zoom(
        self,
        factor
    ):

        if self.imagen_original is None:
            return

        nueva_escala = (
            self.escala
            * factor
        )

        self.escala = max(
            0.05,
            min(
                nueva_escala,
                4.0
            )
        )

        self._mostrar_imagen()

    def _scroll_vertical(
        self,
        event
    ):
        self.canvas.yview_scroll(
            int(-event.delta),
            "units"
        )


    def _scroll_horizontal(
        self,
        event
    ):
        self.canvas.xview_scroll(
            int(-event.delta),
            "units"
        )