import Foundation
import UIKit
import Combine
import CoreImage
import CoreML
import Vision
@preconcurrency import AVFoundation

@MainActor
final class ControlCamara: ObservableObject {
    @Published private(set) var activa = false
    @Published private(set) var ocupada = false
    @Published private(set) var estado = "Lista para iniciar."
    @Published private(set) var imagen: UIImage?
    @Published private(set) var resultados = "Sin analizar."
    @Published private(set) var imagenOriginal: UIImage?
    @Published private(set) var detecciones: [DeteccionIOS] = []
    
    private var solicitud = 0
    
    private lazy var motor = MotorCamara {
        [weak self] imagen, original, texto, detecciones in
        
        guard let self, self.activa else { return }
        
        self.imagen = imagen
        self.imagenOriginal = original
        self.resultados = texto
        self.detecciones = detecciones
    }
    
    func alternar() {
        guard !ocupada else { return }
        
        if activa {
            detener()
        } else {
            Task {
                await iniciar()
            }
        }
    }
    
    private func iniciar() async {
        guard !ocupada, !activa else { return }
        
        ocupada = true
        solicitud += 1
        let solicitudActual = solicitud
        
        defer {
            ocupada = false
        }
        
        let permiso: Bool
        
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            permiso = true
            
        case .notDetermined:
            permiso = await AVCaptureDevice.requestAccess(for: .video)
            
        default:
            permiso = false
        }
        
        guard solicitudActual == solicitud else { return }
        
        guard permiso else {
            estado = "Permití el acceso a la cámara en Ajustes."
            return
        }
        
        guard UIApplication.shared.applicationState == .active else {
            estado = "Volvé a la app para iniciar la cámara."
            return
        }
        
        imagen = nil
        imagenOriginal = nil
        detecciones = []
        resultados = "Preparando modelo..."
        estado = "Iniciando cámara y YOLO..."
        
        let error = await motor.iniciar()
        
        guard solicitudActual == solicitud else {
            motor.detener()
            return
        }
        
        activa = error == nil
        estado = error ?? "Cámara trasera y YOLO activos."
        
        if let error {
            resultados = error
        }
    }
    
    func detener() {
        solicitud += 1
        activa = false
        motor.detener()
        imagen = nil
        imagenOriginal = nil
        estado = "Cámara detenida."
        detecciones = []
    }
}

nonisolated final class MotorCamara:
    NSObject,
    AVCaptureVideoDataOutputSampleBufferDelegate,
    @unchecked Sendable
{
    private let sesion = AVCaptureSession()
    private let colaSesion = DispatchQueue(label: "senales.camara")
    private let colaFrames = DispatchQueue(label: "senales.frames")
    
    private let salida = AVCaptureVideoDataOutput()
    private let contexto = CIContext()
    
    // Configuración en colaSesion; inferencia en colaFrames.
    private var configurada = false
    private var solicitudYOLO: VNCoreMLRequest?
    private var ultimoFrame: Double = 0
    
    private let entregar:
    @MainActor @Sendable (
        UIImage,
        UIImage,
        String,
        [DeteccionIOS]
    ) -> Void
    
    init(
        entregar: @escaping @MainActor @Sendable (
            UIImage,
            UIImage,
            String,
            [DeteccionIOS]
        ) -> Void
    ) {
        self.entregar = entregar
        super.init()
    }
    
    func iniciar() async -> String? {
        await withCheckedContinuation { continuation in
            colaSesion.async {
                if !self.configurada {
                    if let error = self.configurar() {
                        continuation.resume(returning: error)
                        return
                    }
                }
                
                if !self.sesion.isRunning {
                    self.sesion.startRunning()
                }
                
                continuation.resume(
                    returning: self.sesion.isRunning
                    ? nil
                    : "No se pudo iniciar la cámara."
                )
            }
        }
    }
    
    func detener() {
        colaSesion.async {
            if self.sesion.isRunning {
                self.sesion.stopRunning()
            }
        }
    }
    
    private func configurar() -> String? {
        guard let dispositivo = AVCaptureDevice.default(
            .builtInWideAngleCamera,
            for: .video,
            position: .back
        ) else {
            return "No se encontró la cámara trasera."
        }
        
        do {
            let entrada = try AVCaptureDeviceInput(device: dispositivo)
            
            sesion.beginConfiguration()
            defer {
                sesion.commitConfiguration()
            }
            
            if sesion.canSetSessionPreset(.hd1280x720) {
                sesion.sessionPreset = .hd1280x720
            }
            
            guard sesion.canAddInput(entrada) else {
                return "No se pudo conectar la cámara."
            }
            
            sesion.addInput(entrada)
            
            salida.alwaysDiscardsLateVideoFrames = true
            salida.videoSettings = [
                kCVPixelBufferPixelFormatTypeKey as String:
                    kCVPixelFormatType_32BGRA
            ]
            
            salida.setSampleBufferDelegate(self, queue: colaFrames)
            
            guard sesion.canAddOutput(salida) else {
                sesion.removeInput(entrada)
                return "No se pudo agregar la salida de video."
            }
            
            sesion.addOutput(salida)
            configurada = true
            
            return nil
        } catch {
            return "Error de cámara: \(error.localizedDescription)"
        }
    }
    
    private func cargarModelo() throws -> VNCoreMLRequest {
        if let solicitudYOLO {
            return solicitudYOLO
        }
        
        guard let url = Bundle.main.url(
            forResource: "senales_v0_2_1",
            withExtension: "mlmodelc"
        ) else {
            throw NSError(
                domain: "SenalesCampo",
                code: 1,
                userInfo: [
                    NSLocalizedDescriptionKey:
                        "No se encontró senales_v0_2_1 en la app. "
                    + "Revisá el nombre y Target Membership del modelo."
                ]
            )
        }
        
        let configuracion = MLModelConfiguration()
        configuracion.computeUnits = .all
        
        let modelo = try MLModel(
            contentsOf: url,
            configuration: configuracion
        )
        
        let modeloVision = try VNCoreMLModel(for: modelo)
        let solicitud = VNCoreMLRequest(model: modeloVision)
        
        solicitud.imageCropAndScaleOption = .scaleFit
        solicitudYOLO = solicitud
        
        return solicitud
    }
    
    private func detectar(
        en imagen: CGImage
    ) throws -> (
        texto: String,
        imagen: UIImage,
        detecciones: [DeteccionIOS]
    ) {
        let solicitud = try cargarModelo()
        
        let inicio = ProcessInfo.processInfo.systemUptime
        
        let manejador = VNImageRequestHandler(
            cgImage: imagen,
            orientation: .up,
            options: [:]
        )
        
        try manejador.perform([solicitud])
        
        let milisegundos = (
            ProcessInfo.processInfo.systemUptime - inicio
        ) * 1000
        
        guard let observaciones = solicitud.results else {
            throw NSError(
                domain: "SenalesCampo",
                code: 2,
                userInfo: [
                    NSLocalizedDescriptionKey:
                        "El modelo no devolvió resultados."
                ]
            )
        }
        
        guard observaciones.isEmpty
                || observaciones.allSatisfy({
                    $0 is VNRecognizedObjectObservation
                })
                else {
            throw NSError(
                domain: "SenalesCampo",
                code: 3,
                userInfo: [
                    NSLocalizedDescriptionKey:
                        "La salida no es de detección para Vision. "
                    + "Revisá la exportación con nms=True."
                ]
            )
        }
        
        let objetos = observaciones
            .compactMap { $0 as? VNRecognizedObjectObservation }
            .filter {
                ($0.labels.first?.confidence ?? 0) >= 0.25
            }
            .sorted {
                ($0.labels.first?.confidence ?? 0)
                > ($1.labels.first?.confidence ?? 0)
            }
        
        let limitesImagen = CGRect(
            x: 0,
            y: 0,
            width: CGFloat(imagen.width),
            height: CGFloat(imagen.height)
        )
        
        let detecciones: [DeteccionIOS] = objetos.compactMap { objeto in
            guard let etiqueta = objeto.labels.first else {
                return nil
            }
            
            let caja = objeto.boundingBox
            
            let pixeles = CGRect(
                x: caja.minX * limitesImagen.width,
                y: (1 - caja.maxY) * limitesImagen.height,
                width: caja.width * limitesImagen.width,
                height: caja.height * limitesImagen.height
            )
                .intersection(limitesImagen)
            
            guard !pixeles.isNull,
                  pixeles.width > 0,
                  pixeles.height > 0
                    else {
                return nil
            }
            
            return DeteccionIOS(
                id: UUID(),
                claseNombre: etiqueta.identifier,
                confianza: Double(etiqueta.confidence),
                bboxX1: Int(floor(pixeles.minX)),
                bboxY1: Int(floor(pixeles.minY)),
                bboxX2: Int(ceil(pixeles.maxX)),
                bboxY2: Int(ceil(pixeles.maxY))
            )
        }
        
        var lineas = [
            "Inferencia Vision: \(String(format: "%.0f", milisegundos)) ms",
            "Detecciones: \(objetos.count)"
        ]
        
        if objetos.isEmpty {
            lineas.append("\nSin señales detectadas.")
        }
        
        let ancho = CGFloat(imagen.width)
        let alto = CGFloat(imagen.height)
        let tamano = CGSize(width: ancho, height: alto)
        
        let formato = UIGraphicsImageRendererFormat()
        formato.scale = 1
        formato.opaque = true
        
        let renderizador = UIGraphicsImageRenderer(
            size: tamano,
            format: formato
        )
        
        let resultado = renderizador.image { contexto in
            UIImage(cgImage: imagen).draw(
                in: CGRect(origin: .zero, size: tamano)
            )
            
            let grosor = max(3, ancho / 180)
            let fuente = UIFont.boldSystemFont(
                ofSize: max(18, ancho / 35)
            )
            
            for (indice, objeto) in objetos.enumerated() {
                guard let etiqueta = objeto.labels.first else {
                    continue
                }
                
                let confianza = String(
                    format: "%.1f",
                    Double(etiqueta.confidence) * 100
                )
                
                let texto = "\(etiqueta.identifier) \(confianza)%"
                
                lineas.append(
                    "\n\(indice + 1). \(texto)"
                )
                
                // Vision usa origen inferior izquierdo.
                // Para dibujar usamos origen superior izquierdo.
                let caja = objeto.boundingBox
                
                let rectangulo = CGRect(
                    x: caja.minX * ancho,
                    y: (1 - caja.maxY) * alto,
                    width: caja.width * ancho,
                    height: caja.height * alto
                ).intersection(
                    CGRect(origin: .zero, size: tamano)
                )
                
                guard !rectangulo.isNull,
                      rectangulo.width > 0,
                      rectangulo.height > 0
                        else {
                    continue
                }
                
                contexto.cgContext.setStrokeColor(
                    UIColor.systemGreen.cgColor
                )
                contexto.cgContext.setLineWidth(grosor)
                contexto.cgContext.stroke(rectangulo)
                
                let atributos: [NSAttributedString.Key: Any] = [
                    .font: fuente,
                    .foregroundColor: UIColor.black
                ]
                
                let textoNSString = texto as NSString
                let medida = textoNSString.size(
                    withAttributes: atributos
                )
                
                let anchoEtiqueta = min(ancho, medida.width + 12)
                let altoEtiqueta = medida.height + 8
                
                let x = min(
                    max(0, rectangulo.minX),
                    ancho - anchoEtiqueta
                )
                
                let y = max(
                    0,
                    rectangulo.minY - altoEtiqueta
                )
                
                let fondo = CGRect(
                    x: x,
                    y: y,
                    width: anchoEtiqueta,
                    height: altoEtiqueta
                )
                
                contexto.cgContext.setFillColor(
                    UIColor.systemGreen.cgColor
                )
                contexto.cgContext.fill(fondo)
                
                contexto.cgContext.saveGState()
                contexto.cgContext.clip(to: fondo)
                
                textoNSString.draw(
                    at: CGPoint(x: x + 6, y: y + 4),
                    withAttributes: atributos
                )
                
                contexto.cgContext.restoreGState()
            }
        }
        
        return (
            texto: lineas.joined(separator: "\n"),
            imagen: resultado,
            detecciones: detecciones
        )
    }
    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        // Procesa como máximo unas 5 muestras por segundo.
        // Los frames atrasados se descartan.
        let ahora = ProcessInfo.processInfo.systemUptime
        
        guard ahora - ultimoFrame >= 0.2 else {
            return
        }
        
        ultimoFrame = ahora
        
        autoreleasepool {
            guard let buffer = CMSampleBufferGetImageBuffer(
                sampleBuffer
            ) else {
                return
            }
            
            // Primera prueba con el iPhone en vertical.
            let frame = CIImage(cvPixelBuffer: buffer)
                .oriented(.right)
            
            guard let cgImage = contexto.createCGImage(
                frame,
                from: frame.extent
            ) else {
                return
            }
            
            let texto: String
            let imagen: UIImage
            let detecciones: [DeteccionIOS]
            
            do {
                let resultado = try detectar(en: cgImage)
                texto = resultado.texto
                imagen = resultado.imagen
                detecciones = resultado.detecciones
            } catch {
                texto = "Error de YOLO:\n\(error.localizedDescription)"
                imagen = UIImage(cgImage: cgImage)
                detecciones = []
            }
            
            let original = UIImage(cgImage: cgImage)
            let actualizar = entregar
            
            Task { @MainActor in
                actualizar(imagen, original, texto, detecciones)
            }
        }
    }
}
