import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var apiService: APIService

    @State private var username = ""
    @State private var password = ""
    @State private var isSubmitting = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()

                Image("Logo")
                    .resizable()
                    .scaledToFit()
                    .frame(maxWidth: 320)
                    .accessibilityLabel("Shows")

                Text("Sign in to manage your lists, search for shows, and get AI recommendations.")
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)

                VStack(spacing: 16) {
                    TextField("Username", text: $username)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textFieldStyle(.roundedBorder)
                        .submitLabel(.next)

                    SecureField("Password", text: $password)
                        .textFieldStyle(.roundedBorder)
                        .submitLabel(.go)
                        .onSubmit {
                            submit()
                        }
                }

                if let message = apiService.authErrorMessage {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                }

                Button(action: submit) {
                    HStack(spacing: 8) {
                        if isSubmitting {
                            ProgressView()
                                .tint(.white)
                        }

                        Text(isSubmitting ? "Signing In..." : "Sign In")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Color.accentColor)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .disabled(isSubmitting || username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || password.isEmpty)

                Spacer()
            }
            .padding(24)
            .navigationTitle("Login")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onChange(of: username) { _, _ in
            apiService.clearAuthError()
        }
        .onChange(of: password) { _, _ in
            apiService.clearAuthError()
        }
    }

    private func submit() {
        guard !isSubmitting else { return }

        isSubmitting = true

        Task {
            _ = await apiService.login(
                username: username.trimmingCharacters(in: .whitespacesAndNewlines),
                password: password
            )
            isSubmitting = false
        }
    }
}
