import Foundation

nonisolated struct CapturaPendiente: Codable, Identifiable, Sendable {
    let id: UUID
    let usuarioID: String
    let fechaSeleccion: Date

    let latitud: Double
    let longitud: Double
    let precisionMetros: Double
    let fechaUbicacion: Date
    let fuenteUbicacion: String

    let versionModelo: String
    let resumenDetecciones: String
    // Opcional para poder leer las capturas antiguas.
    let detecciones: [DeteccionIOS]?

    let rostrosTapados: Int
    let placasTapadas: Int

    // Solo contiene la imagen que salió del anonimizador.
    let evidenciaJPEG: Data

    var intentos: Int = 0
    var proximoIntento: Date?
    var ultimoError: String?

    // Opcionales para mantener compatibilidad con archivos anteriores.
    var deteccionesEnviadas: [UUID]?
    var versionModeloID: UUID?
    var bloqueada: Bool?
}

nonisolated struct DeteccionIOS: Codable, Identifiable, Sendable {
    let id: UUID
    let claseNombre: String
    let confianza: Double

    // Coordenadas en píxeles del frame original orientado.
    let bboxX1: Int
    let bboxY1: Int
    let bboxX2: Int
    let bboxY2: Int
}
