import Foundation
import UIKit
import Combine

actor AlmacenColaIOS {
    private func carpeta() throws -> URL {
        let base = try FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )

        let directorio = base.appendingPathComponent(
            "ColaDetecciones",
            isDirectory: true
        )

        try FileManager.default.createDirectory(
            at: directorio,
            withIntermediateDirectories: true,
            attributes: nil
        )

        // La cola es almacenamiento local operativo.
        // No se incorpora al respaldo de iCloud.
        var url = directorio
        var atributos = URLResourceValues()
        atributos.isExcludedFromBackup = true
        try url.setResourceValues(atributos)

        return directorio
    }

    func guardar(_ captura: CapturaPendiente) throws {
        let archivo = try carpeta().appendingPathComponent(
            "\(captura.id.uuidString).json"
        )

        let codificador = JSONEncoder()
        codificador.dateEncodingStrategy = .iso8601

        let datos = try codificador.encode(captura)

        try datos.write(
            to: archivo,
            options: [
                .atomic,
                .completeFileProtectionUntilFirstUserAuthentication
            ]
        )
    }

    func eliminar(id: UUID) throws {
        let archivo = try carpeta().appendingPathComponent("\(id.uuidString).json")
        if FileManager.default.fileExists(atPath: archivo.path) {
            try FileManager.default.removeItem(at: archivo)
        }
    }

    func listar(usuarioID: String) throws -> [CapturaPendiente] {
        let archivos = try FileManager.default.contentsOfDirectory(
            at: carpeta(),
            includingPropertiesForKeys: nil,
            options: [.skipsHiddenFiles]
        )

        let decodificador = JSONDecoder()
        decodificador.dateDecodingStrategy = .iso8601

        var pendientes: [CapturaPendiente] = []

        for archivo in archivos where archivo.pathExtension == "json" {
            let datos = try Data(contentsOf: archivo)
            let captura: CapturaPendiente

            do {
                captura = try decodificador.decode(
                    CapturaPendiente.self,
                    from: datos
                )
            } catch {
                // No borramos archivos que no se pueden leer.
                throw NSError(
                    domain: "ColaIOS",
                    code: 1,
                    userInfo: [
                        NSLocalizedDescriptionKey:
                            "No se pudo leer \(archivo.lastPathComponent). "
                            + "El archivo se conservó."
                    ]
                )
            }

            if captura.usuarioID == usuarioID {
                pendientes.append(captura)
            }
        }

        return pendientes.sorted {
            $0.fechaSeleccion < $1.fechaSeleccion
        }
    }
}

@MainActor
final class ColaLocalIOS: ObservableObject {
    @Published private(set) var pendientes: [CapturaPendiente] = []
    @Published private(set) var error = ""
    @Published private(set) var estado = "Cola sin revisar."
    @Published private(set) var enviando = false
    private var eliminando = false

    private let almacen = AlmacenColaIOS()
    private let api = EnvioDeteccionesIOS()

    func cargar(usuarioID: String) async {
        guard !enviando else { return }
        error = ""
        do {
            pendientes = try await almacen.listar(usuarioID: usuarioID)
            estado = "Cola revisada: \(pendientes.count) capturas."
        } catch {
            self.error = error.localizedDescription
            estado = "No se pudo revisar la cola. Los archivos se conservaron."
        }
    }

    private func actualizarLista(_ captura: CapturaPendiente) {
        pendientes.removeAll { $0.id == captura.id }
        pendientes.append(captura)
        pendientes.sort { $0.fechaSeleccion < $1.fechaSeleccion }
    }

    func guardar(_ captura: CapturaPendiente) async throws {
        try await almacen.guardar(captura)
        actualizarLista(captura)
        estado = "Captura guardada en el teléfono."
    }
    
    func eliminarPendiente(id: UUID, usuarioID: String) async {
        guard !enviando, !eliminando,
              pendientes.contains(where: { $0.id == id && $0.usuarioID == usuarioID })
        else { return }

        eliminando = true
        defer { eliminando = false }

        do {
            try await almacen.eliminar(id: id)
            pendientes.removeAll { $0.id == id }
            error = ""
            estado = "Captura eliminada de la cola local."
        } catch {
            self.error = error.localizedDescription
        }
    }

    func sincronizar(sesion: SesionAPI, manual: Bool = false) async {
        guard !enviando, !eliminando, !Task.isCancelled,
              sesion.token != nil, !sesion.usuarioID.isEmpty,
              UIApplication.shared.applicationState == .active
        else { return }

        let propietario = sesion.usuarioID
        enviando = true
        error = ""
        defer { enviando = false }

        let lote: [CapturaPendiente]
        do {
            lote = try await almacen.listar(usuarioID: propietario)
            pendientes = lote
        } catch {
            self.error = error.localizedDescription
            return
        }

        guard !lote.isEmpty else {
            if manual { estado = "No hay capturas pendientes para este usuario." }
            return
        }

        var confirmadas = 0
        var revisadas = 0

        for inicial in lote {
            guard !Task.isCancelled, sesion.usuarioID == propietario,
                  sesion.token != nil,
                  UIApplication.shared.applicationState == .active
            else { break }

            if !manual {
                if inicial.bloqueada == true { continue }
                if let fecha = inicial.proximoIntento, fecha > Date() { continue }
            }

            guard let detecciones = inicial.detecciones, !detecciones.isEmpty else {
                // Capturas antiguas: no inventamos clases ni coordenadas desde el texto.
                continue
            }

            revisadas += 1
            var captura = inicial
            estado = "Enviando captura \(captura.id.uuidString.prefix(8))..."

            do {
                if captura.versionModeloID == nil {
                    let id = try await api.obtenerModelo(
                        version: captura.versionModelo,
                        sesion: sesion,
                        propietario: propietario
                    )
                    captura.versionModeloID = id
                    try await almacen.guardar(captura)
                }

                let clases = try await api.obtenerClases(
                    sesion: sesion,
                    propietario: propietario
                )

                for deteccion in detecciones {
                    if (captura.deteccionesEnviadas ?? []).contains(deteccion.id) {
                        continue
                    }

                    try Task.checkCancellation()

                    try await api.enviar(
                        deteccion: deteccion,
                        captura: captura,
                        clases: clases,
                        sesion: sesion,
                        propietario: propietario
                    )

                    // Confirmamos cada señal en disco antes de continuar.
                    var enviadas = captura.deteccionesEnviadas ?? []
                    enviadas.append(deteccion.id)
                    captura.deteccionesEnviadas = enviadas
                    captura.ultimoError = nil
                    captura.proximoIntento = nil
                    captura.bloqueada = false
                    try await almacen.guardar(captura)
                    actualizarLista(captura)
                    confirmadas += 1
                }

                // Se elimina solo cuando todas las señales fueron confirmadas.
                try await almacen.eliminar(id: captura.id)
                pendientes.removeAll { $0.id == captura.id }
            } catch {
                if error is CancellationError {
                    estado = "Envío detenido. Los pendientes se conservaron."
                    break
                }

                if let fallo = error as? FalloEnvioIOS, fallo.codigo == 401 {
                    self.error = "La sesión cambió o expiró. Volvé a iniciar sesión."
                    break
                }

                captura.intentos += 1
                captura.ultimoError = error.localizedDescription

                if let fallo = error as? FalloEnvioIOS {
                    captura.bloqueada = !fallo.reintentable
                } else {
                    captura.bloqueada = false
                }

                let demora = min(300.0, 5.0 * pow(2.0, Double(min(captura.intentos - 1, 6))))
                captura.proximoIntento = Date().addingTimeInterval(demora)

                do {
                    try await almacen.guardar(captura)
                    actualizarLista(captura)
                } catch {
                    self.error = "No se pudo actualizar la cola: \(error.localizedDescription)"
                    break
                }
            }
        }

        if revisadas > 0 || manual {
            estado = "Confirmadas: \(confirmadas) señales. Pendientes: \(pendientes.count) capturas."
            if pendientes.contains(where: { $0.detecciones == nil }) {
                estado += " Hay capturas antiguas sin datos estructurados; se conservan."
            }
        }
    }
}
