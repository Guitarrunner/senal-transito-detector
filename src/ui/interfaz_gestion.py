import tkinter as tk
from tkinter import messagebox

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

        self.sesion_expirada = False
        self.sesion_cerrada = False

        self.contenido_actual = None

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

        self._limpiar_contenido_actual()

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