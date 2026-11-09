import Foundation
import Combine
import CoreLocation

@MainActor
final class ControlUbicacion:
    NSObject,
    ObservableObject,
    @preconcurrency CLLocationManagerDelegate
{
    @Published private(set) var ubicacion: CLLocation?
    @Published private(set) var estado = "GPS sin iniciar."

    private let gestor = CLLocationManager()
    private var solicitado = false

    override init() {
        super.init()

        gestor.delegate = self
        gestor.desiredAccuracy = kCLLocationAccuracyBest
        gestor.distanceFilter = kCLDistanceFilterNone
    }

    func iniciar() {
        solicitado = true
        actualizarAutorizacion()
    }

    func detener() {
        solicitado = false
        gestor.stopUpdatingLocation()
        ubicacion = nil
        estado = "GPS detenido."
    }

    private func actualizarAutorizacion() {
        guard solicitado else { return }

        switch gestor.authorizationStatus {
        case .notDetermined:
            estado = "Esperando permiso de ubicación."
            gestor.requestWhenInUseAuthorization()

        case .authorizedWhenInUse, .authorizedAlways:
            estado = "Buscando ubicación..."
            gestor.startUpdatingLocation()

        case .denied:
            gestor.stopUpdatingLocation()
            ubicacion = nil
            estado = "Ubicación denegada. Revisá Ajustes."

        case .restricted:
            gestor.stopUpdatingLocation()
            ubicacion = nil
            estado = "Ubicación restringida."

        @unknown default:
            ubicacion = nil
            estado = "Estado de ubicación desconocido."
        }
    }

    func locationManagerDidChangeAuthorization(
        _ manager: CLLocationManager
    ) {
        actualizarAutorizacion()
    }

    func locationManager(
        _ manager: CLLocationManager,
        didUpdateLocations locations: [CLLocation]
    ) {
        guard solicitado,
              let nueva = locations.max(
                by: { $0.timestamp < $1.timestamp }
              ),
              CLLocationCoordinate2DIsValid(nueva.coordinate),
              nueva.coordinate.latitude.isFinite,
              nueva.coordinate.longitude.isFinite,
              nueva.horizontalAccuracy.isFinite,
              nueva.horizontalAccuracy >= 0
        else {
            return
        }

        if let anterior = ubicacion,
           nueva.timestamp < anterior.timestamp {
            return
        }

        ubicacion = nueva
        estado = "Ubicación recibida."
    }

    func locationManager(
        _ manager: CLLocationManager,
        didFailWithError error: Error
    ) {
        guard solicitado else { return }

        if let errorGPS = error as? CLError,
           errorGPS.code == .locationUnknown {
            estado = "Buscando ubicación..."
            return
        }

        ubicacion = nil
        estado = "Error GPS: \(error.localizedDescription)"
    }

    func resumen(ahora: Date) -> String {
        guard let ubicacion else {
            return estado
        }

        let edad = ahora.timeIntervalSince(ubicacion.timestamp)
        let precision = ubicacion.horizontalAccuracy

        // Criterios iniciales de la app, iguales a los del escritorio.
        let valida = edad >= 0
            && edad <= 30
            && precision <= 100

        let latitud = String(
            format: "%.6f",
            ubicacion.coordinate.latitude
        )

        let longitud = String(
            format: "%.6f",
            ubicacion.coordinate.longitude
        )

        let metros = String(format: "%.0f", precision)
        let segundos = String(format: "%.1f", max(0, edad))

        return """
        GPS: \(valida ? "lectura válida" : "lectura no válida")
        Latitud: \(latitud)
        Longitud: \(longitud)
        Precisión estimada: \(metros) m
        Antigüedad: \(segundos) s
        """
    }
}
