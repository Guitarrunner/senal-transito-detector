import tkinter as tk

from src.domain.usuario import Usuario
from src.domain.rol_usuario import RolUsuario


class InterfazGestion:

    def __init__(self, usuario_autenticado: Usuario):

        self.usuario_autenticado = usuario_autenticado

        self.ventana = tk.Tk()

        self.ventana.title(
            "Sistema de Gestión de Señales"
        )

        self.ventana.geometry("1200x750")

        self.centrar_ventana(1200, 750)

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


        # ===== USUARIO =====

        label_usuario = tk.Label(
            sidebar,
            text=(
                f"Usuario: "
                f"{self.usuario_autenticado.nombre_usuario}\n"
                f"Rol: "
                f"{self.usuario_autenticado.rol.value}"
            ),
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
            fg="#333333",
            justify="left"
        )

        label_usuario.pack(
            pady=(15, 20)
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
            text="Gestión de señales",
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
            bg="#f0f0f0"
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

        self.titulo_contenido.config(
            text="Detecciones pendientes"
        )

        self.texto_contenido.config(
            text=(
                "Aquí se mostrarán las detecciones "
                "pendientes de revisión."
            )
        )

        self.label_estado.config(
            text="Consultando detecciones."
        )


    def mostrar_inventario(self):

        self.titulo_contenido.config(
            text="Inventario"
        )

        self.texto_contenido.config(
            text=(
                "Aquí se mostrará el inventario "
                "georeferenciado de señales."
            )
        )

        self.label_estado.config(
            text="Consultando inventario."
        )


    def mostrar_mapa(self):

        self.titulo_contenido.config(
            text="Mapa"
        )

        self.texto_contenido.config(
            text=(
                "Aquí se mostrará la interfaz "
                "cartográfica."
            )
        )

        self.label_estado.config(
            text="Mostrando mapa."
        )


    def mostrar_usuarios(self):

        self.titulo_contenido.config(
            text="Gestión de usuarios"
        )

        self.texto_contenido.config(
            text=(
                "Aquí se administrarán los usuarios "
                "del sistema."
            )
        )


    def mostrar_modelos(self):

        self.titulo_contenido.config(
            text="Modelos"
        )

        self.texto_contenido.config(
            text=(
                "Aquí se gestionarán las versiones "
                "del modelo."
            )
        )


    def mostrar_dataset(self):

        self.titulo_contenido.config(
            text="Dataset"
        )

        self.texto_contenido.config(
            text=(
                "Aquí se gestionará la información "
                "relacionada con el dataset."
            )
        )


    def ejecutar(self):

        self.ventana.mainloop()