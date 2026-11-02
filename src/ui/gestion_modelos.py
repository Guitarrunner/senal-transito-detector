import tkinter as tk

from tkinter import (
    messagebox,
    ttk
)

from src.gestion.cliente_api import (
    SesionExpiradaError
)


class GestionModelos(tk.Frame):

    def __init__(
        self,
        parent,
        cliente_api,
        callback_estado=None
    ):
        super().__init__(
            parent
        )

        self.cliente_api = cliente_api
        self.callback_estado = (
            callback_estado
        )

        self.datasets = []
        self.entrenamientos = []
        self.modelos = []

        self.actualizacion_programada = None

        self._crear_componentes()
        self._cargar_datasets()
        self._cargar_entrenamientos()
        self._cargar_modelos()

        self._programar_actualizacion()

    def _crear_componentes(self):


        frame_formulario = ttk.LabelFrame(
            self,
            text="Nuevo entrenamiento"
        )

        frame_formulario.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ttk.Label(
            frame_formulario,
            text="Dataset:"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="e"
        )

        self.combo_dataset = ttk.Combobox(
            frame_formulario,
            state="readonly",
            width=35
        )

        self.combo_dataset.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="w"
        )

        ttk.Label(
            frame_formulario,
            text="Versión:"
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="e"
        )

        self.version_var = tk.StringVar(
            value="v0.1"
        )

        self.entry_version = ttk.Entry(
            frame_formulario,
            textvariable=self.version_var,
            width=20
        )

        self.entry_version.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
            sticky="w"
        )

        ttk.Label(
            frame_formulario,
            text="Modelo base:"
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
            sticky="e"
        )

        self.modelo_var = tk.StringVar(
            value="yolov8n.pt"
        )

        self.combo_modelo = ttk.Combobox(
            frame_formulario,
            textvariable=self.modelo_var,
            state="readonly",
            values=[
                "yolov8n.pt",
                "yolov8s.pt",
                "yolov8m.pt",
                "yolov8l.pt",
                "yolov8x.pt",
            ],
            width=18
        )

        self.combo_modelo.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        ttk.Label(
            frame_formulario,
            text="Épocas:"
        ).grid(
            row=1,
            column=2,
            padx=5,
            pady=5,
            sticky="e"
        )

        self.epocas_var = tk.IntVar(
            value=50
        )

        self.spin_epocas = ttk.Spinbox(
            frame_formulario,
            from_=1,
            to=500,
            textvariable=self.epocas_var,
            width=10
        )

        self.spin_epocas.grid(
            row=1,
            column=3,
            padx=5,
            pady=5,
            sticky="w"
        )

        ttk.Label(
            frame_formulario,
            text="Tamaño imagen:"
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=5,
            sticky="e"
        )

        self.imgsz_var = tk.IntVar(
            value=640
        )

        self.combo_imgsz = ttk.Combobox(
            frame_formulario,
            textvariable=self.imgsz_var,
            state="readonly",
            values=[
                320,
                480,
                640,
                800,
                960,
            ],
            width=18
        )

        self.combo_imgsz.grid(
            row=2,
            column=1,
            padx=5,
            pady=5,
            sticky="w"
        )

        # Batch

        ttk.Label(
            frame_formulario,
            text="Batch:"
        ).grid(
            row=2,
            column=2,
            padx=5,
            pady=5,
            sticky="e"
        )

        self.batch_var = tk.IntVar(
            value=8
        )

        self.combo_batch = ttk.Combobox(
            frame_formulario,
            textvariable=self.batch_var,
            state="readonly",
            values=[
                2,
                4,
                8,
                16,
                32,
            ],
            width=18
        )

        self.combo_batch.grid(
            row=2,
            column=3,
            padx=5,
            pady=5,
            sticky="w"
        )

        self.boton_entrenar = ttk.Button(
            frame_formulario,
            text="Iniciar entrenamiento",
            command=self._iniciar_entrenamiento
        )

        self.boton_entrenar.grid(
            row=3,
            column=0,
            columnspan=4,
            pady=15
        )

        frame_progreso = ttk.LabelFrame(
            self,
            text="Estado actual"
        )

        frame_progreso.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.label_progreso = ttk.Label(
            frame_progreso,
            text="Sin entrenamiento activo."
        )

        self.label_progreso.pack(
            pady=(10, 5)
        )

        self.barra_progreso = ttk.Progressbar(
            frame_progreso,
            orient="horizontal",
            mode="determinate",
            maximum=100
        )

        self.barra_progreso.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        frame_historial = ttk.LabelFrame(
            self,
            text="Entrenamientos"
        )

        frame_historial.pack(
            fill="both",
            padx=10,
            pady=10
        )

        self.tabla = ttk.Treeview(
            frame_historial,
            height=5,
            columns=(
                "version",
                "modelo",
                "estado",
                "progreso",
                "epocas",
                "imgsz",
                "batch",
            ),
            show="headings"
        )

        self.tabla.heading(
            "version",
            text="Versión"
        )

        self.tabla.heading(
            "modelo",
            text="Modelo"
        )

        self.tabla.heading(
            "estado",
            text="Estado"
        )

        self.tabla.heading(
            "progreso",
            text="Progreso"
        )

        self.tabla.heading(
            "epocas",
            text="Épocas"
        )

        self.tabla.heading(
            "imgsz",
            text="Imagen"
        )

        self.tabla.heading(
            "batch",
            text="Batch"
        )

        self.tabla.column(
            "version",
            width=100
        )

        self.tabla.column(
            "modelo",
            width=120
        )

        self.tabla.column(
            "estado",
            width=120
        )

        self.tabla.column(
            "progreso",
            width=100,
            anchor="center"
        )

        self.tabla.column(
            "epocas",
            width=70,
            anchor="center"
        )

        self.tabla.column(
            "imgsz",
            width=70,
            anchor="center"
        )

        self.tabla.column(
            "batch",
            width=70,
            anchor="center"
        )

        self.tabla.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        frame_modelos = ttk.LabelFrame(
            self,
            text="Modelos entrenados"
        )

        frame_modelos.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.tabla_modelos = ttk.Treeview(
            frame_modelos,
            columns=(
                "version",
                "dataset",
                "precision",
                "recall",
                "map50",
                "map5095",
                "latencia",
                "fps",
                "estado",
            ),
            show="headings",
            height=8
        )

        columnas = {
            "version": "Versión",
            "dataset": "Dataset",
            "precision": "Precisión",
            "recall": "Recall",
            "map50": "mAP50",
            "map5095": "mAP50-95",
            "latencia": "Latencia ms",
            "fps": "FPS",
            "estado": "Estado",
        }

        for columna, titulo in columnas.items():
            self.tabla_modelos.heading(
                columna,
                text=titulo
            )

        self.tabla_modelos.column(
            "version",
            width=100
        )

        self.tabla_modelos.column(
            "dataset",
            width=160
        )

        self.tabla_modelos.column(
            "precision",
            width=90,
            anchor="center"
        )

        self.tabla_modelos.column(
            "recall",
            width=90,
            anchor="center"
        )

        self.tabla_modelos.column(
            "map50",
            width=90,
            anchor="center"
        )

        self.tabla_modelos.column(
            "map5095",
            width=100,
            anchor="center"
        )

        self.tabla_modelos.column(
            "latencia",
            width=100,
            anchor="center"
        )

        self.tabla_modelos.column(
            "fps",
            width=80,
            anchor="center"
        )

        self.tabla_modelos.column(
            "estado",
            width=90,
            anchor="center"
        )

        self.tabla_modelos.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        self.boton_activar_modelo = (
            ttk.Button(
                frame_modelos,
                text="Activar modelo seleccionado",
                command=self._activar_modelo
            )
        )

        self.boton_activar_modelo.pack(
            pady=(5, 10)
        )

    def _cargar_datasets(self):

        try:
            self.datasets = (
                self.cliente_api
                .listar_datasets()
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        nombres = [
            dataset["nombre"]
            for dataset in self.datasets
        ]

        self.combo_dataset[
            "values"
        ] = nombres

        if nombres:
            self.combo_dataset.current(
                0
            )

    def _cargar_entrenamientos(self):

        try:
            self.entrenamientos = (
                self.cliente_api.listar_entrenamientos()
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:
            if self.callback_estado:
                self.callback_estado(
                    str(error)
                )

            return

        self._actualizar_tabla()
        self._actualizar_progreso()

    def _cargar_modelos(self):

        try:
            self.modelos = (
                self.cliente_api
                .listar_modelos()
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:

            if self.callback_estado:
                self.callback_estado(
                    str(error)
                )

            return

        self._actualizar_tabla_modelos()

    def _actualizar_tabla(self):

        for item in self.tabla.get_children():
            self.tabla.delete(
                item
            )

        for entrenamiento in (
            self.entrenamientos
        ):

            epoca_actual = (
                entrenamiento[
                    "epoca_actual"
                ]
            )

            epocas = entrenamiento[
                "epocas"
            ]

            progreso = (
                f"{epoca_actual}/{epocas}"
            )

            self.tabla.insert(
                "",
                tk.END,
                values=(
                    entrenamiento[
                        "version"
                    ],
                    entrenamiento[
                        "modelo_base"
                    ],
                    entrenamiento[
                        "estado"
                    ],
                    progreso,
                    epocas,
                    entrenamiento[
                        "imgsz"
                    ],
                    entrenamiento[
                        "batch"
                    ],
                )
            )

    def _iniciar_entrenamiento(self):

        indice_dataset = (
            self.combo_dataset.current()
        )

        if indice_dataset < 0:
            messagebox.showwarning(
                "Sin dataset",
                "Seleccione un dataset."
            )
            return

        version = (
            self.version_var
            .get()
            .strip()
        )

        if not version:
            messagebox.showwarning(
                "Versión",
                "Ingrese una versión."
            )
            return

        dataset = self.datasets[
            indice_dataset
        ]

        confirmar = messagebox.askyesno(
            "Iniciar entrenamiento",
            (
                "¿Desea iniciar el "
                "entrenamiento?\n\n"
                f"Dataset: "
                f"{dataset['nombre']}\n"
                f"Versión: {version}\n"
                f"Modelo: "
                f"{self.modelo_var.get()}\n"
                f"Épocas: "
                f"{self.epocas_var.get()}"
            )
        )

        if not confirmar:
            return

        try:
            entrenamiento = (
                self.cliente_api
                .iniciar_entrenamiento(
                    dataset_id=(
                        dataset["id"]
                    ),
                    version=version,
                    modelo_base=(
                        self.modelo_var.get()
                    ),
                    epocas=(
                        self.epocas_var.get()
                    ),
                    imgsz=(
                        self.imgsz_var.get()
                    ),
                    batch=(
                        self.batch_var.get()
                    )
                )
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        if self.callback_estado:
            self.callback_estado(
                (
                    "Entrenamiento "
                    f"{version} iniciado."
                )
            )

        messagebox.showinfo(
            "Entrenamiento iniciado",
            (
                "El entrenamiento fue "
                "iniciado correctamente.\n\n"
                "Puede continuar utilizando "
                "la interfaz mientras se ejecuta."
            )
        )

        self._cargar_entrenamientos()

    def _actualizar_progreso(self):

        entrenamiento_activo = None

        for entrenamiento in (
            self.entrenamientos
        ):
            if entrenamiento[
                "estado"
            ] in (
                "PENDIENTE",
                "ENTRENANDO"
            ):
                entrenamiento_activo = (
                    entrenamiento
                )
                break

        if entrenamiento_activo is None:

            self.label_progreso.config(
                text=(
                    "Sin entrenamiento activo."
                )
            )

            self.barra_progreso[
                "value"
            ] = 0

            self.boton_entrenar.config(
                state="normal"
            )

            return

        estado = entrenamiento_activo[
            "estado"
        ]

        epoca_actual = (
            entrenamiento_activo[
                "epoca_actual"
            ]
        )

        epocas = entrenamiento_activo[
            "epocas"
        ]

        if estado == "PENDIENTE":

            texto = (
                "Preparando dataset..."
            )

            porcentaje = 0

        else:

            texto = (
                f"Entrenando "
                f"{entrenamiento_activo['version']} "
                f"- época "
                f"{epoca_actual}/{epocas}"
            )

            if epocas > 0:
                porcentaje = (
                    epoca_actual
                    / epocas
                    * 100
                )
            else:
                porcentaje = 0

        self.label_progreso.config(
            text=texto
        )

        self.barra_progreso[
            "value"
        ] = porcentaje

        # Evita lanzar dos entrenamientos
        # simultáneamente desde la interfaz.
        self.boton_entrenar.config(
            state="disabled"
        )

    def _programar_actualizacion(self):

        self.actualizacion_programada = (
            self.after(
                3000,
                self._actualizar_automaticamente
            )
        )

    def _actualizar_automaticamente(self):

        if not self.winfo_exists():
            return

        self._cargar_entrenamientos()
        self._cargar_modelos()

        self._programar_actualizacion()

    def destroy(self):

        if (
            self.actualizacion_programada
            is not None
        ):
            try:
                self.after_cancel(
                    self.actualizacion_programada
                )
            except tk.TclError:
                pass

        super().destroy()

    def _nombre_dataset(
        self,
        dataset_id: str
    ) -> str:

        for dataset in self.datasets:

            if (
                str(dataset["id"])
                == str(dataset_id)
            ):
                return dataset["nombre"]

        return str(dataset_id)[:8]


    def _formatear_metrica(
        self,
        valor,
        decimales=3
    ):

        if valor is None:
            return "-"

        return f"{valor:.{decimales}f}"

    def _actualizar_tabla_modelos(self):

        for item in (
            self.tabla_modelos
            .get_children()
        ):
            self.tabla_modelos.delete(
                item
            )

        for modelo in self.modelos:

            estado = (
                "ACTIVO"
                if modelo["activo"]
                else "Inactivo"
            )

            dataset_nombre = (
                self._nombre_dataset(
                    modelo["dataset_id"]
                )
            )

            self.tabla_modelos.insert(
                "",
                tk.END,

                # Usamos el UUID real como ID
                # de la fila.
                iid=str(
                    modelo["id"]
                ),

                values=(
                    modelo["version"],

                    dataset_nombre,

                    self._formatear_metrica(
                        modelo["precision"]
                    ),

                    self._formatear_metrica(
                        modelo["recall"]
                    ),

                    self._formatear_metrica(
                        modelo["map_50"]
                    ),

                    self._formatear_metrica(
                        modelo["map_50_95"]
                    ),

                    self._formatear_metrica(
                        modelo[
                            "latencia_promedio_ms"
                        ],
                        2
                    ),

                    self._formatear_metrica(
                        modelo["fps"],
                        1
                    ),

                    estado
                )
            )

    def _activar_modelo(self):

        seleccion = (
            self.tabla_modelos
            .selection()
        )

        if not seleccion:
            messagebox.showwarning(
                "Modelo",
                (
                    "Seleccione un modelo "
                    "para activar."
                )
            )
            return

        modelo_id = seleccion[0]

        modelo = next(
            (
                modelo
                for modelo in self.modelos
                if str(modelo["id"])
                == modelo_id
            ),
            None
        )

        if modelo is None:
            return

        if modelo["activo"]:

            messagebox.showinfo(
                "Modelo activo",
                (
                    f"La versión "
                    f"{modelo['version']} "
                    "ya se encuentra activa."
                )
            )

            return

        confirmar = messagebox.askyesno(
            "Activar modelo",
            (
                "¿Desea activar esta versión?\n\n"
                f"Versión: "
                f"{modelo['version']}\n"
                f"mAP50: "
                f"{self._formatear_metrica(modelo['map_50'])}\n"
                f"mAP50-95: "
                f"{self._formatear_metrica(modelo['map_50_95'])}\n\n"
                "El modelo actualmente activo "
                "será reemplazado."
            )
        )

        if not confirmar:
            return

        try:
            self.cliente_api.activar_modelo(
                modelo_id
            )

        except SesionExpiradaError:
            return

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )
            return

        self._cargar_modelos()

        if self.callback_estado:
            self.callback_estado(
                (
                    "Modelo "
                    f"{modelo['version']} "
                    "activado."
                )
            )

        messagebox.showinfo(
            "Modelo activado",
            (
                f"La versión "
                f"{modelo['version']} "
                "es ahora el modelo activo."
            )
        )