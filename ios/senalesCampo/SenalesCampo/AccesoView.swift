import SwiftUI

struct AccesoView: View {
    @StateObject private var sesion = SesionAPI()

    @State private var usuario = ""
    @State private var password = ""

    @FocusState private var focoPassword: Bool

    var body: some View {
        Group {
            if sesion.token != nil {
                VStack(spacing: 0) {
                    HStack {
                        Text(
                            "\(sesion.nombreUsuario) · \(sesion.rol)"
                        )
                        .font(.caption)

                        Spacer()

                        Button("Cerrar sesión") {
                            sesion.cerrarSesion()
                        }
                        .font(.caption)
                    }
                    .padding()

                    ContentView()
                        .environmentObject(sesion)
                }
            } else {
                formularioLogin
            }
        }
    }

    private var formularioLogin: some View {
        VStack(spacing: 20) {
            Text("Señales Campo")
                .font(.largeTitle.bold())

            Text("Iniciá sesión con tu usuario del sistema.")
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            TextField("Usuario", text: $usuario)
                .textContentType(.username)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .textFieldStyle(.roundedBorder)
                .disabled(sesion.ocupada)

            SecureField("Contraseña", text: $password)
                .textContentType(.password)
                .textFieldStyle(.roundedBorder)
                .focused($focoPassword)
                .disabled(sesion.ocupada)
                .onSubmit {
                    ingresar()
                }

            if !sesion.error.isEmpty {
                Text(sesion.error)
                    .foregroundStyle(.red)
                    .font(.footnote)
                    .multilineTextAlignment(.center)
            }

            Button {
                ingresar()
            } label: {
                HStack {
                    if sesion.ocupada {
                        ProgressView()
                    }

                    Text(
                        sesion.ocupada
                            ? "Ingresando..."
                            : "Iniciar sesión"
                    )
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(sesion.ocupada)
        }
        .padding(24)
        .frame(maxWidth: 450)
    }

    private func ingresar() {
        guard !sesion.ocupada else { return }

        Task {
            await sesion.iniciarSesion(
                usuario: usuario,
                password: password
            )

            password = ""

            if sesion.token == nil {
                focoPassword = true
            }
        }
    }
}
