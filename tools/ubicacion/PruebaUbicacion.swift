import Cocoa
import CoreLocation

final class Aplicacion: NSObject,
    NSApplicationDelegate,
    CLLocationManagerDelegate {

    let gestor = CLLocationManager()
    var temporizador: Timer?
    var solicitudPendiente = false
    var ventana: NSWindow!
    var texto: NSTextField!

    func solicitarLectura() {
        guard !solicitudPendiente else {
            return
        }

        solicitudPendiente = true
        gestor.requestLocation()
    }

    func applicationDidFinishLaunching(
        _ notification: Notification
    ) {
        // Etiqueta interna para conservar las asignaciones
        // de estado existentes, sin crear una ventana.
        texto = NSTextField(
            wrappingLabelWithString: ""
        )

        gestor.delegate = self
        gestor.desiredAccuracy = kCLLocationAccuracyBest

        actualizarAutorizacion()
    }

    func locationManagerDidChangeAuthorization(
        _ manager: CLLocationManager
    ) {
        actualizarAutorizacion()
    }

    func actualizarAutorizacion() {
        switch gestor.authorizationStatus {
        case .notDetermined:
            gestor.requestWhenInUseAuthorization()

        case .authorizedAlways, .authorizedWhenInUse:
            guard temporizador == nil else {
                return
            }

            texto.stringValue =
                "Permiso concedido. Buscando ubicación..."

            solicitarLectura()

            temporizador = Timer.scheduledTimer(
                withTimeInterval: 10,
                repeats: true
            ) { [weak self] _ in
                self?.solicitarLectura()
            }

        case .denied, .restricted:
            temporizador?.invalidate()
            temporizador = nil
            solicitudPendiente = false
            gestor.stopUpdatingLocation()

            texto.stringValue =
                "Acceso denegado. Revisá Localización en macOS."

        @unknown default:
            texto.stringValue =
                "Estado de autorización desconocido."
        }
    }

    func locationManager(
        _ manager: CLLocationManager,
        didUpdateLocations locations: [CLLocation]
    ) {
        solicitudPendiente = false
        guard let ubicacion = locations.last else {
            return
        }

        do {
            try publicarUbicacion(ubicacion)
        } catch {
            texto.stringValue =
                "No se pudo compartir la ubicación:\n\(error.localizedDescription)"
            return
        }

        let antiguedad = -ubicacion.timestamp.timeIntervalSinceNow

        guard ubicacion.horizontalAccuracy >= 0,
              antiguedad >= -5,
              antiguedad <= 30 else {
            texto.stringValue =
                "Esperando una ubicación válida y reciente..."
            return
        }

        let fecha = ISO8601DateFormatter().string(
            from: ubicacion.timestamp
        )

        texto.stringValue = """
        Ubicación recibida

        Latitud: \(ubicacion.coordinate.latitude)
        Longitud: \(ubicacion.coordinate.longitude)
        Precisión estimada: \(Int(ubicacion.horizontalAccuracy)) m
        Fecha: \(fecha)
        Fuente: Core Location de macOS
        """
    }

    func locationManager(
        _ manager: CLLocationManager,
        didFailWithError error: Error
    ) {
        solicitudPendiente = false
        texto.stringValue =
            "No se pudo obtener ubicación:\n\(error.localizedDescription)"
    }

    func applicationShouldTerminateAfterLastWindowClosed(
        _ sender: NSApplication
    ) -> Bool {
        return false
    }

    func applicationWillTerminate(
        _ notification: Notification
    ) {
        temporizador?.invalidate()
        gestor.stopUpdatingLocation()
    }

    func publicarUbicacion(_ ubicacion: CLLocation) throws {
        let carpeta = FileManager.default
            .urls(
                for: .applicationSupportDirectory,
                in: .userDomainMask
            )[0]
            .appendingPathComponent("SenalesTFG")

        try FileManager.default.createDirectory(
            at: carpeta,
            withIntermediateDirectories: true,
            attributes: [.posixPermissions: 0o700]
        )

        let datos: [String: Any] = [
            "latitud": ubicacion.coordinate.latitude,
            "longitud": ubicacion.coordinate.longitude,
            "precision_m": ubicacion.horizontalAccuracy,
            "timestamp": ubicacion.timestamp.timeIntervalSince1970,
            "fuente": "core_location_macos"
        ]

        let contenido = try JSONSerialization.data(
            withJSONObject: datos
        )

        try contenido.write(
            to: carpeta.appendingPathComponent("ubicacion.json"),
            options: .atomic
        )
    }
}

let aplicacion = NSApplication.shared
let delegado = Aplicacion()

aplicacion.setActivationPolicy(.accessory)
aplicacion.delegate = delegado
aplicacion.run()