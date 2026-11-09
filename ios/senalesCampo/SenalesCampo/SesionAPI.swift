import Foundation
import Combine

@MainActor
final class SesionAPI: ObservableObject {
    @Published private(set) var token: String?
    @Published private(set) var nombreUsuario = ""
    @Published private(set) var rol = ""
    @Published private(set) var usuarioID = ""
    @Published private(set) var ocupada = false
    @Published private(set) var error = ""

    let servidor: URL? = {
        guard let valor = Bundle.main.object(
            forInfoDictionaryKey: "APIBaseURL"
        ) as? String,
              let componentes = URLComponents(
                string: valor.trimmingCharacters(in: .whitespacesAndNewlines)
              ),
              let esquema = componentes.scheme?.lowercased(),
              ["http", "https"].contains(esquema),
              let host = componentes.host, !host.isEmpty,
              componentes.user == nil, componentes.password == nil,
              componentes.query == nil, componentes.fragment == nil
        else {
            return nil
        }
        return componentes.url
    }()

    private struct EntradaLogin: Encodable {
        let nombre_usuario: String
        let password: String
    }

    private struct UsuarioRespuesta: Decodable {
        let id: String
        let nombre_usuario: String
        let rol: String
    }

    private struct RespuestaLogin: Decodable {
        let access_token: String
        let usuario: UsuarioRespuesta
    }

    private struct ErrorRespuesta: Decodable {
        let detail: String
    }

    func iniciarSesion(
        usuario: String,
        password: String
    ) async {
        guard !ocupada else { return }

        error = ""

        let nombre = usuario.trimmingCharacters(
            in: .whitespacesAndNewlines
        )

        guard !nombre.isEmpty, !password.isEmpty else {
            error = "Ingresá usuario y contraseña."
            return
        }

        guard let servidor else {
            error = "Configurá APIBaseURL en la información del target de Xcode."
            return
        }

        ocupada = true
        defer {
            ocupada = false
        }

        do {
            let url = servidor
                .appendingPathComponent("auth")
                .appendingPathComponent("login")

            var solicitud = URLRequest(url: url)
            solicitud.httpMethod = "POST"
            solicitud.timeoutInterval = 15

            solicitud.setValue(
                "application/json",
                forHTTPHeaderField: "Content-Type"
            )

            solicitud.httpBody = try JSONEncoder().encode(
                EntradaLogin(
                    nombre_usuario: nombre,
                    password: password
                )
            )

            let (datos, respuesta) = try await URLSession.shared.data(
                for: solicitud
            )

            guard let http = respuesta as? HTTPURLResponse else {
                error = "Respuesta no válida del servidor."
                return
            }

            guard (200..<300).contains(http.statusCode) else {
                let detalle = try? JSONDecoder().decode(
                    ErrorRespuesta.self,
                    from: datos
                )

                error = detalle?.detail
                    ?? "Error del servidor: \(http.statusCode)."
                return
            }

            let login = try JSONDecoder().decode(
                RespuestaLogin.self,
                from: datos
            )

            guard !login.access_token.isEmpty else {
                error = "El servidor devolvió un token vacío."
                return
            }

            nombreUsuario = login.usuario.nombre_usuario
            usuarioID = login.usuario.id
            rol = login.usuario.rol
            token = login.access_token
        } catch {
            self.error = "No se pudo iniciar sesión: "
                + error.localizedDescription
        }
    }

    func cerrarSesion() {
        token = nil
        nombreUsuario = ""
        usuarioID = ""
        rol = ""
        error = ""
    }
}
