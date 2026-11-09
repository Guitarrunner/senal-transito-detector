import Foundation
import UIKit

nonisolated struct FalloEnvioIOS: LocalizedError, Sendable {
    let codigo: Int
    let mensaje: String
    let reintentable: Bool

    var errorDescription: String? { mensaje }
}

@MainActor
final class EnvioDeteccionesIOS {
    private struct ClaseAPI: Decodable {
        let id: Int
        let nombre: String
    }

    private struct ModeloAPI: Decodable {
        let id: UUID
        let version: String
    }

    private struct ConfirmacionAPI: Decodable {
        let id: UUID
    }

    private func token(sesion: SesionAPI, propietario: String) throws -> String {
        guard sesion.usuarioID == propietario,
              let token = sesion.token,
              !Task.isCancelled,
              UIApplication.shared.applicationState == .active
        else {
            throw FalloEnvioIOS(
                codigo: 401,
                mensaje: "La sesión no está disponible para este propietario.",
                reintentable: false
            )
        }
        return token
    }

    private func solicitar(
        ruta: String,
        sesion: SesionAPI,
        propietario: String,
        cuerpo: Data? = nil,
        tipo: String? = nil
    ) async throws -> Data {
        let autorizacion = try token(sesion: sesion, propietario: propietario)
        guard let servidor = sesion.servidor else {
            throw FalloEnvioIOS(
                codigo: 0,
                mensaje: "Configurá APIBaseURL en la información del target de Xcode.",
                reintentable: false
            )
        }
        var solicitud = URLRequest(
            url: servidor.appendingPathComponent(ruta)
        )
        solicitud.httpMethod = cuerpo == nil ? "GET" : "POST"
        solicitud.timeoutInterval = 30
        solicitud.setValue("Bearer \(autorizacion)", forHTTPHeaderField: "Authorization")
        solicitud.setValue("application/json", forHTTPHeaderField: "Accept")
        if let tipo {
            solicitud.setValue(tipo, forHTTPHeaderField: "Content-Type")
        }
        solicitud.httpBody = cuerpo

        let (datos, respuesta) = try await URLSession.shared.data(for: solicitud)
        guard let http = respuesta as? HTTPURLResponse else {
            throw FalloEnvioIOS(codigo: 0, mensaje: "Respuesta HTTP no válida.", reintentable: true)
        }

        guard (200..<300).contains(http.statusCode) else {
            var detalle = "Error HTTP \(http.statusCode)."
            if let json = try? JSONSerialization.jsonObject(with: datos) as? [String: Any],
               let valor = json["detail"] {
                detalle += " \(valor)"
            }
            throw FalloEnvioIOS(
                codigo: http.statusCode,
                mensaje: detalle,
                reintentable: http.statusCode >= 500
                    || [408, 425, 429].contains(http.statusCode)
            )
        }
        return datos
    }

    func obtenerModelo(
        version: String,
        sesion: SesionAPI,
        propietario: String
    ) async throws -> UUID {
        let datos = try await solicitar(
            ruta: "modelos/activo", sesion: sesion, propietario: propietario
        )
        let modelo = try JSONDecoder().decode(ModeloAPI.self, from: datos)

        func normalizar(_ texto: String) -> String {
            let limpio = texto.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            return limpio.hasPrefix("v") ? String(limpio.dropFirst()) : limpio
        }

        guard normalizar(modelo.version) == normalizar(version) else {
            throw FalloEnvioIOS(
                codigo: 400,
                mensaje: "El teléfono usó \(version), pero el modelo activo es \(modelo.version). No se envió con una versión incorrecta.",
                reintentable: false
            )
        }
        return modelo.id
    }

    func obtenerClases(
        sesion: SesionAPI,
        propietario: String
    ) async throws -> [String: Int] {
        let datos = try await solicitar(
            ruta: "clases", sesion: sesion, propietario: propietario
        )
        let clases = try JSONDecoder().decode([ClaseAPI].self, from: datos)
        var mapa: [String: Int] = [:]
        for clase in clases {
            let nombre = clase.nombre.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            guard mapa[nombre] == nil else {
                throw FalloEnvioIOS(codigo: 400, mensaje: "Nombre de clase duplicado: \(nombre).", reintentable: false)
            }
            mapa[nombre] = clase.id
        }
        return mapa
    }

    func enviar(
        deteccion: DeteccionIOS,
        captura: CapturaPendiente,
        clases: [String: Int],
        sesion: SesionAPI,
        propietario: String
    ) async throws {
        guard captura.usuarioID == propietario,
              let modeloID = captura.versionModeloID else {
            throw FalloEnvioIOS(codigo: 400, mensaje: "Propietario o modelo no válido.", reintentable: false)
        }

        let nombre = deteccion.claseNombre.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard let claseID = clases[nombre] else {
            throw FalloEnvioIOS(codigo: 400, mensaje: "No existe la clase activa '\(deteccion.claseNombre)' en la API.", reintentable: false)
        }

        guard !captura.evidenciaJPEG.isEmpty,
              deteccion.confianza.isFinite,
              (0...1).contains(deteccion.confianza),
              deteccion.bboxX1 >= 0, deteccion.bboxY1 >= 0,
              deteccion.bboxX2 > deteccion.bboxX1,
              deteccion.bboxY2 > deteccion.bboxY1,
              captura.latitud.isFinite, captura.longitud.isFinite,
              (-90...90).contains(captura.latitud),
              (-180...180).contains(captura.longitud),
              captura.precisionMetros.isFinite, captura.precisionMetros >= 0
        else {
            throw FalloEnvioIOS(codigo: 400, mensaje: "La captura tiene datos no válidos.", reintentable: false)
        }

        let formatoFecha = ISO8601DateFormatter()
        let campos = [
            "id_local": deteccion.id.uuidString,
            "clase_senal_id": String(claseID),
            "confianza": String(deteccion.confianza),
            "bbox_x1": String(deteccion.bboxX1),
            "bbox_y1": String(deteccion.bboxY1),
            "bbox_x2": String(deteccion.bboxX2),
            "bbox_y2": String(deteccion.bboxY2),
            "version_modelo_id": modeloID.uuidString,
            "latitud_captura": String(captura.latitud),
            "longitud_captura": String(captura.longitud),
            "precision_ubicacion_m": String(captura.precisionMetros),
            "fecha_ubicacion": formatoFecha.string(from: captura.fechaUbicacion),
            "fuente_ubicacion": captura.fuenteUbicacion,
            "anonimizada": "true"
        ]

        let separador = "Boundary-\(UUID().uuidString)"
        var cuerpo = Data()
        func agregar(_ texto: String) {
            cuerpo.append(contentsOf: texto.utf8)
        }

        for clave in campos.keys.sorted() {
            agregar("--\(separador)\r\n")
            agregar("Content-Disposition: form-data; name=\"\(clave)\"\r\n\r\n")
            agregar("\(campos[clave]!)\r\n")
        }

        agregar("--\(separador)\r\n")
        agregar("Content-Disposition: form-data; name=\"evidencia\"; filename=\"\(captura.id.uuidString).jpg\"\r\n")
        agregar("Content-Type: image/jpeg\r\n\r\n")
        cuerpo.append(captura.evidenciaJPEG)
        agregar("\r\n--\(separador)--\r\n")

        let datos = try await solicitar(
            ruta: "detecciones",
            sesion: sesion,
            propietario: propietario,
            cuerpo: cuerpo,
            tipo: "multipart/form-data; boundary=\(separador)"
        )

        let confirmacion = try JSONDecoder().decode(ConfirmacionAPI.self, from: datos)
        guard confirmacion.id == deteccion.id else {
            throw FalloEnvioIOS(codigo: 0, mensaje: "El servidor confirmó otro identificador. Se conservó la captura.", reintentable: true)
        }
    }
}
