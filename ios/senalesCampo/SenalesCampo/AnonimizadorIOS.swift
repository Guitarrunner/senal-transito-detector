import Foundation
import UIKit
import CoreImage
import CoreML
import Vision

nonisolated final class AnonimizadorIOS: @unchecked Sendable {
    private let cola = DispatchQueue(label: "senales.anonimizacion")

    private var modelos: [
        String: (
            modelo: VNCoreMLModel,
            ancho: CGFloat,
            alto: CGFloat
        )
    ] = [:]

    func procesar(
        _ imagen: UIImage
    ) async throws -> (imagen: UIImage, rostros: Int, placas: Int) {
        try await withCheckedThrowingContinuation { continuacion in
            cola.async {
                do {
                    let resultado = try self.procesarEnCola(imagen)
                    continuacion.resume(returning: resultado)
                } catch {
                    continuacion.resume(throwing: error)
                }
            }
        }
    }

    private func cargarModelo(
        nombre: String
    ) throws -> (
        modelo: VNCoreMLModel,
        ancho: CGFloat,
        alto: CGFloat
    ) {
        if let existente = modelos[nombre] {
            return existente
        }

        guard let url = Bundle.main.url(
            forResource: nombre,
            withExtension: "mlmodelc"
        ) else {
            throw fallo("No se encontró \(nombre) en la app.")
        }

        let configuracion = MLModelConfiguration()
        configuracion.computeUnits = .all

        let modelo = try MLModel(
            contentsOf: url,
            configuration: configuracion
        )

        guard let entrada = modelo.modelDescription
            .inputDescriptionsByName.values
            .compactMap({ $0.imageConstraint })
            .first
        else {
            throw fallo("\(nombre) no tiene una entrada de imagen.")
        }

        let datos = (
            modelo: try VNCoreMLModel(for: modelo),
            ancho: CGFloat(entrada.pixelsWide),
            alto: CGFloat(entrada.pixelsHigh)
        )

        modelos[nombre] = datos
        return datos
    }

    private func procesarEnCola(
        _ imagen: UIImage
    ) throws -> (imagen: UIImage, rostros: Int, placas: Int) {
        guard let original = imagen.cgImage else {
            throw fallo("La captura no contiene una imagen válida.")
        }

        let ancho = CGFloat(original.width)
        let alto = CGFloat(original.height)
        let limites = CGRect(x: 0, y: 0, width: ancho, height: alto)

        var cajas: [CGRect] = []
        var rostros = 0
        var placas = 0

        for nombre in ["rostros_ios", "placas_ios"] {
            let datos = try cargarModelo(nombre: nombre)
            let solicitud = VNCoreMLRequest(model: datos.modelo)
            solicitud.imageCropAndScaleOption = .scaleFit

            let manejador = VNImageRequestHandler(
                cgImage: original,
                orientation: .up,
                options: [:]
            )

            try manejador.perform([solicitud])

            guard let resultados = solicitud.results else {
                throw fallo("\(nombre) no devolvió resultados.")
            }

            let detectadas: [CGRect]

            if resultados.isEmpty {
                detectadas = []
            } else if resultados.allSatisfy({
                $0 is VNRecognizedObjectObservation
            }) {
                detectadas = resultados
                    .compactMap {
                        $0 as? VNRecognizedObjectObservation
                    }
                    .compactMap { objeto -> CGRect? in
                        guard let etiqueta = objeto.labels.first,
                              etiqueta.confidence >= 0.25
                        else {
                            return nil
                        }

                        let caja = objeto.boundingBox

                        return CGRect(
                            x: caja.minX * ancho,
                            y: (1 - caja.maxY) * alto,
                            width: caja.width * ancho,
                            height: caja.height * alto
                        )
                    }
            } else if nombre == "rostros_ios" {
                let matrices = resultados
                    .compactMap {
                        $0 as? VNCoreMLFeatureValueObservation
                    }
                    .compactMap {
                        $0.featureValue.multiArrayValue
                    }

                guard let matriz = matrices.first(where: {
                    $0.shape.count == 3
                        && $0.shape[0].intValue == 1
                        && $0.shape[1].intValue == 20
                }) else {
                    throw fallo(
                        "La salida de rostros no tiene forma [1, 20, N]."
                    )
                }

                detectadas = decodificarRostros(
                    matriz,
                    anchoImagen: ancho,
                    altoImagen: alto,
                    anchoEntrada: datos.ancho,
                    altoEntrada: datos.alto
                )
            } else {
                throw fallo(
                    "Salida de placas no compatible. "
                    + "Necesitamos revisar su formato."
                )
            }

            for caja in detectadas {
                let ampliada = caja.insetBy(
                    dx: -caja.width * 0.15,
                    dy: -caja.height * 0.15
                )
                .integral
                .intersection(limites)

                guard !ampliada.isNull,
                      ampliada.width > 0,
                      ampliada.height > 0
                else {
                    continue
                }

                cajas.append(ampliada)

                if nombre == "rostros_ios" {
                    rostros += 1
                } else {
                    placas += 1
                }
            }
        }

        let formato = UIGraphicsImageRendererFormat()
        formato.scale = 1
        formato.opaque = true

        let renderizador = UIGraphicsImageRenderer(
            size: limites.size,
            format: formato
        )

        let salida = renderizador.image { contexto in
            UIImage(cgImage: original).draw(in: limites)
            contexto.cgContext.setFillColor(UIColor.black.cgColor)

            for caja in cajas {
                contexto.cgContext.fill(caja)
            }
        }

        return (salida, rostros, placas)
    }

    private func decodificarRostros(
        _ matriz: MLMultiArray,
        anchoImagen: CGFloat,
        altoImagen: CGFloat,
        anchoEntrada: CGFloat,
        altoEntrada: CGFloat
    ) -> [CGRect] {
        // Salida YOLO pose:
        // centro X, centro Y, ancho, alto, confianza,
        // y después los 15 valores de puntos faciales.
        let cantidad = matriz.shape[2].intValue

        // Deshace el escalado proporcional y el relleno
        // centrado usados con .scaleFit.
        let escala = min(
            anchoEntrada / anchoImagen,
            altoEntrada / altoImagen
        )

        let margenX = (anchoEntrada - anchoImagen * escala) / 2
        let margenY = (altoEntrada - altoImagen * escala) / 2

        let limites = CGRect(
            x: 0,
            y: 0,
            width: anchoImagen,
            height: altoImagen
        )

        func valor(_ canal: Int, _ indice: Int) -> Double {
            matriz[
                [
                    NSNumber(value: 0),
                    NSNumber(value: canal),
                    NSNumber(value: indice)
                ]
            ].doubleValue
        }

        var candidatas: [(caja: CGRect, confianza: Double)] = []

        for indice in 0..<cantidad {
            let confianza = valor(4, indice)

            guard confianza.isFinite,
                  confianza >= 0.25
            else {
                continue
            }

            let cx = valor(0, indice)
            let cy = valor(1, indice)
            let ancho = valor(2, indice)
            let alto = valor(3, indice)

            guard cx.isFinite,
                  cy.isFinite,
                  ancho.isFinite,
                  alto.isFinite,
                  ancho > 0,
                  alto > 0
            else {
                continue
            }

            let caja = CGRect(
                x: (CGFloat(cx - ancho / 2) - margenX) / escala,
                y: (CGFloat(cy - alto / 2) - margenY) / escala,
                width: CGFloat(ancho) / escala,
                height: CGFloat(alto) / escala
            )
            .intersection(limites)

            guard !caja.isNull,
                  caja.width > 0,
                  caja.height > 0
            else {
                continue
            }

            candidatas.append((caja, confianza))
        }

        // NMS: evita contar muchas cajas del mismo rostro.
        candidatas.sort { $0.confianza > $1.confianza }

        var seleccionadas: [CGRect] = []

        for candidata in candidatas {
            let repetida = seleccionadas.contains {
                interseccionSobreUnion($0, candidata.caja) > 0.45
            }

            if !repetida {
                seleccionadas.append(candidata.caja)
            }
        }

        return seleccionadas
    }

    private func interseccionSobreUnion(
        _ primera: CGRect,
        _ segunda: CGRect
    ) -> CGFloat {
        let interseccion = primera.intersection(segunda)

        guard !interseccion.isNull else {
            return 0
        }

        let areaInterseccion = interseccion.width * interseccion.height

        let union = primera.width * primera.height
            + segunda.width * segunda.height
            - areaInterseccion

        return union > 0 ? areaInterseccion / union : 0
    }

    private func fallo(_ mensaje: String) -> NSError {
        NSError(
            domain: "AnonimizadorIOS",
            code: 1,
            userInfo: [
                NSLocalizedDescriptionKey: mensaje
            ]
        )
    }
}
