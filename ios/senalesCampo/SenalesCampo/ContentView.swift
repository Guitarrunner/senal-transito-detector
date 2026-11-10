import SwiftUI
import UIKit
import Foundation
import CoreLocation

struct ContentView: View {
    @StateObject private var camara = ControlCamara()
    @StateObject private var gps = ControlUbicacion()
    @State private var capturaImagen: UIImage?
    @State private var capturaResumen = ""
    @State private var avisoCaptura = ""
    @State private var anonimizando = false
    @State private var anonimizador = AnonimizadorIOS()
    @EnvironmentObject private var sesion: SesionAPI
    @StateObject private var cola = ColaLocalIOS()
    @Environment(\.scenePhase) private var escena
    @State private var capturaParaEliminar: CapturaPendiente?
    
    
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Text("Señales Campo")
                    .font(.title2.bold())
                
                VStack(alignment: .leading, spacing: 6) {
                    Text("Pendientes de envío: \(cola.pendientes.count)")
                        .font(.headline)
                    
                    Text("Señales pendientes: \(cantidadSenalesEnCola)")
                    .font(.footnote)
                    
                    if !cola.error.isEmpty {
                        Text(cola.error)
                            .font(.footnote)
                            .foregroundStyle(.red)
                    }
                    
                    Text(cola.estado)
                        .font(.footnote)

                    HStack {
                        Button("Revisar cola local") {
                            Task {
                                await cola.cargar(usuarioID: sesion.usuarioID)
                            }
                        }

                        Button(cola.enviando ? "Enviando..." : "Enviar pendientes") {
                            Task {
                                await cola.sincronizar(sesion: sesion, manual: true)
                            }
                        }
                    }
                    .disabled(cola.enviando)

                    ForEach(cola.pendientes) { captura in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(captura.fechaSeleccion.formatted(date: .abbreviated, time: .shortened))
                                Text(captura.id.uuidString.prefix(8))
                                    .foregroundStyle(.secondary)

                                if let error = captura.ultimoError {
                                    Text(error).foregroundStyle(.orange)
                                }
                            }
                            .font(.caption)

                            Spacer()

                            Button("Eliminar", role: .destructive) {
                                capturaParaEliminar = captura
                            }
                            .disabled(cola.enviando)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                
                TimelineView(.periodic(from: .now, by: 1)) { tiempo in
                    Text(gps.resumen(ahora: tiempo.date))
                        .font(.system(.caption, design: .monospaced))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                        .background(Color.secondary.opacity(0.1))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                
                ZStack {
                    Color.black
                    
                    if let imagen = camara.imagen {
                        Image(uiImage: imagen)
                            .resizable()
                            .scaledToFit()
                    }
                    
                    if !camara.activa {
                        Text("Cámara detenida")
                            .foregroundStyle(.white)
                    }
                }
                .frame(maxWidth: .infinity)
                .frame(height: 420)
                .clipShape(RoundedRectangle(cornerRadius: 16))
                
                Text(camara.estado)
                    .font(.footnote)
                    .multilineTextAlignment(.center)
                
                Button {
                    camara.alternar()
                } label: {
                    Label(
                        camara.activa
                        ? "Detener cámara"
                        : "Iniciar cámara",
                        systemImage: camara.activa
                        ? "stop.fill"
                        : "camera.fill"
                    )
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(camara.ocupada)
                
                Button {
                    capturarDeteccion()
                } label: {
                    Label("Capturar detección", systemImage: "camera.viewfinder")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .disabled(
                    !camara.activa
                    || camara.imagenOriginal == nil
                    || anonimizando
                )
                
                if !avisoCaptura.isEmpty {
                    Text(avisoCaptura)
                        .font(.footnote)
                }
                
                if let capturaImagen {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Última captura")
                            .font(.headline)
                        
                        Image(uiImage: capturaImagen)
                            .resizable()
                            .scaledToFit()
                            .frame(maxHeight: 300)
                        
                        Text(capturaResumen)
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                        
                        Button("Ocultar vista de captura") {
                            self.capturaImagen = nil
                            capturaResumen = ""
                            avisoCaptura = ""
                        }
                    }
                    .padding()
                    .background(Color.secondary.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Detecciones")
                        .font(.headline)
                    
                    Text(camara.resultados)
                        .font(.system(.footnote, design: .monospaced))
                        .textSelection(.enabled)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(Color.secondary.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .padding()
        }
        .alert(item: $capturaParaEliminar) { captura in
            Alert(
                title: Text("¿Eliminar captura pendiente?"),
                message: Text("Se borrará la copia guardada en este iPhone."),
                primaryButton: .destructive(Text("Eliminar")) {
                    Task {
                        await cola.eliminarPendiente(
                            id: captura.id,
                            usuarioID: sesion.usuarioID
                        )
                    }
                },
                secondaryButton: .cancel()
            )
        }
        .onAppear {
            gps.iniciar()
        }
        .onChange(of: escena) { _, nueva in
            if nueva == .background {
                camara.detener()
                gps.detener()
            } else if nueva == .active {
                gps.iniciar()
            }
        }
        .onDisappear {
            camara.detener()
            gps.detener()
        }
        
        .task(id: sesion.usuarioID) {
            await cola.cargar(usuarioID: sesion.usuarioID)
            while !Task.isCancelled {
                if escena == .active {
                    await cola.sincronizar(sesion: sesion)
                }
                do {
                    try await Task.sleep(for: .seconds(15))
                } catch {
                    break
                }
            }
        }
    }
    
    private var cantidadSenalesEnCola: Int {
        cola.pendientes.reduce(0) { total, captura in
            total + (captura.detecciones ?? []).filter {
                !(captura.deteccionesEnviadas ?? []).contains($0.id)
            }.count
        }
    }

    private func capturarDeteccion() {
        guard !anonimizando,
              camara.activa,
              let original = camara.imagenOriginal
                else {
            return
        }
        
        guard sesion.token != nil, !sesion.usuarioID.isEmpty else {
            avisoCaptura = "Iniciá sesión antes de capturar."
            return
        }
        
        // Conservamos el propietario aunque la sesión cambie
        // mientras se procesa la imagen.
        let propietarioID = sesion.usuarioID
        
        let ahora = Date()
        
        guard let ubicacion = gps.ubicacion else {
            avisoCaptura = "Esperá una lectura de ubicación."
            return
        }
        
        let edad = ahora.timeIntervalSince(ubicacion.timestamp)
        let precision = ubicacion.horizontalAccuracy
        
        guard edad >= 0,
              edad <= 30,
              precision.isFinite,
              precision >= 0,
              precision <= 100
                else {
            avisoCaptura = "La ubicación es antigua o poco precisa."
            return
        }
        
        guard camara.resultados.hasPrefix("Inferencia Vision:") else {
            avisoCaptura = "Esperá un resultado válido de YOLO."
            return
        }
        
        // Congelamos los datos antes de iniciar el trabajo asíncrono.
        let resultados = camara.resultados
        // Cada captura manual recibe IDs propios. Luego se conservan al reintentar.
        let detecciones = camara.detecciones.map { deteccion in
            DeteccionIOS(
                id: UUID(),
                claseNombre: deteccion.claseNombre,
                confianza: deteccion.confianza,
                bboxX1: deteccion.bboxX1,
                bboxY1: deteccion.bboxY1,
                bboxX2: deteccion.bboxX2,
                bboxY2: deteccion.bboxY2
            )
        }
        
        guard !detecciones.isEmpty else {
            avisoCaptura = "No hay señales detectadas para guardar."
            return
        }
        let identificador = UUID()
        
        capturaImagen = nil
        capturaResumen = ""
        anonimizando = true
        avisoCaptura = "Anonimizando rostros y placas..."
        
        Task { @MainActor in
            defer {
                anonimizando = false
            }
            
            do {
                let resultado = try await anonimizador.procesar(original)
                
                guard let jpeg = resultado.imagen.jpegData(
                    compressionQuality: 0.9
                ) else {
                    throw NSError(
                        domain: "ColaIOS",
                        code: 2,
                        userInfo: [
                            NSLocalizedDescriptionKey:
                                "No se pudo convertir la evidencia a JPEG."
                        ]
                    )
                }
                
                let pendiente = CapturaPendiente(
                    id: identificador,
                    usuarioID: propietarioID,
                    fechaSeleccion: ahora,
                    latitud: ubicacion.coordinate.latitude,
                    longitud: ubicacion.coordinate.longitude,
                    precisionMetros: precision,
                    fechaUbicacion: ubicacion.timestamp,
                    fuenteUbicacion: "core_location_ios",
                    versionModelo: "v1.0",
                    resumenDetecciones: resultados,
                    detecciones: detecciones,
                    rostrosTapados: resultado.rostros,
                    placasTapadas: resultado.placas,
                    evidenciaJPEG: jpeg
                )
                
                try await cola.guardar(pendiente)
                
                capturaImagen = resultado.imagen
                
                capturaResumen = """
                ID: \(identificador)
                Fecha de selección: \(ahora.formatted())
                
                \(resultados)
                
                Latitud: \(String(format: "%.6f", ubicacion.coordinate.latitude))
                Longitud: \(String(format: "%.6f", ubicacion.coordinate.longitude))
                Precisión estimada: \(String(format: "%.0f", precision)) m
                Fecha de ubicación: \(ubicacion.timestamp.formatted())
                Fuente: Core Location iOS
                
                Rostros tapados: \(resultado.rostros)
                Placas tapadas: \(resultado.placas)
                """
                
                avisoCaptura = "Captura guardada en la cola local."
            } catch {
                capturaImagen = nil
                capturaResumen = ""
                avisoCaptura = "No se completó la captura: "
                + error.localizedDescription
            }
        }
    }
    
    
}
