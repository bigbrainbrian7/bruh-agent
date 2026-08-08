import AppKit
import SwiftUI

struct PrivacyOnboardingView: View {
    let onAccessConfirmed: () -> Void

    @State private var hasAcknowledgedPrivacy = false
    @State private var isCheckingAccess = false
    @State private var accessError: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack(alignment: .top, spacing: 14) {
                Image(systemName: "lock.shield")
                    .font(.system(size: 34))
                    .foregroundStyle(.blue)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Allow access to Messages")
                        .font(.title2)
                        .fontWeight(.semibold)
                    Text("Bruh Agent needs Full Disk Access to read your local Messages database.")
                        .foregroundStyle(.secondary)
                }
            }

            GroupBox("What this permission means") {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Full Disk Access is a broad macOS permission. Bruh Agent itself only reads ~/Library/Messages/chat.db to analyze conversations you choose to track; it does not change that database.")
                    Text("macOS does not let an app grant itself this permission. You must enable Bruh Agent in System Settings > Privacy & Security > Full Disk Access.")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .font(.callout)
            }

            GroupBox("Where your data goes") {
                VStack(alignment: .leading, spacing: 8) {
                    Label("With Ollama, analyzed messages stay on this Mac.", systemImage: "desktopcomputer")
                    Label("With Gemini, the messages sent for analysis are sent to Google.", systemImage: "cloud")
                    Label("Plans and scan state are stored locally. Your Gemini API key is stored in macOS Keychain.", systemImage: "key")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .font(.callout)
            }

            Toggle(
                "I understand that Full Disk Access is a broad system permission.",
                isOn: $hasAcknowledgedPrivacy
            )

            if let accessError {
                Text(accessError)
                    .font(.callout)
                    .foregroundStyle(.red)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack {
                Button("Open Full Disk Access Settings") {
                    NSWorkspace.shared.open(
                        URL(fileURLWithPath: "/System/Applications/System Settings.app")
                    )
                }

                Spacer()

                Button {
                    checkAccess()
                } label: {
                    if isCheckingAccess {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Text("Check access")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(!hasAcknowledgedPrivacy || isCheckingAccess)
            }
        }
        .padding(24)
        .frame(width: 600)
    }

    private func checkAccess() {
        isCheckingAccess = true
        accessError = nil

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                _ = try BackendClient().listChats(limit: 1)
                DispatchQueue.main.async {
                    isCheckingAccess = false
                    onAccessConfirmed()
                }
            } catch {
                DispatchQueue.main.async {
                    isCheckingAccess = false
                    accessError = "Bruh Agent still cannot read your Messages database. Enable Bruh Agent in Full Disk Access, then try again.\n\nDetails: \(error.localizedDescription)"
                }
            }
        }
    }
}
