//
//  ContentView.swift
//  BruhAgent
//
//  Created by Brian Yu on 8/5/26.
//

import Foundation
import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            PlansView()
                .tabItem {
                    Label("Plans", systemImage: "checklist")
                }

            ChatsView()
                .tabItem {
                    Label("Chats", systemImage: "message")
                }
        }
        .frame(minWidth: 560, minHeight: 420)
    }
}

private struct PlansView: View {
    private let keychain = KeychainStore()

    @State private var plans: [Plan] = []
    @State private var status = "Ready to scan your tracked chats."
    @State private var errorMessage: String?
    @State private var isScanning = false
    @State private var provider: ModelProvider = .ollama
    @State private var ollamaModels: [OllamaModel] = []
    @State private var ollamaModel = ""
    @State private var isLoadingOllamaModels = false
    @State private var ollamaError: String?
    @State private var geminiModel = CloudProvider.gemini.defaultModel
    @State private var geminiAPIKey = ""
    @State private var isGeminiAPIKeyVisible = false
    @State private var hasSavedGeminiAPIKey = false
    @State private var keychainError: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Plans")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                Spacer()

                Button("Scan chats") {
                    scanChats()
                }
                .disabled(isScanning || isLoadingOllamaModels || (provider == .ollama && ollamaModels.isEmpty))
            }

            Text(status)
                .foregroundStyle(.secondary)

            GroupBox("Model") {
                VStack(alignment: .leading, spacing: 10) {
                    Picker("Provider", selection: $provider) {
                        ForEach(ModelProvider.allCases) { provider in
                            Text(provider.displayName).tag(provider)
                        }
                    }
                    .pickerStyle(.menu)

                    if provider == .ollama {
                        if isLoadingOllamaModels {
                            ProgressView("Checking Ollama…")
                        } else if let ollamaError {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("Ollama unavailable")
                                    .fontWeight(.semibold)
                                Text(ollamaError)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Button("Reload models") {
                                    Task { await loadOllamaModels() }
                                }
                            }
                        } else if ollamaModels.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("No Ollama models installed.")
                                    .fontWeight(.semibold)
                                Text("Install a model with `ollama pull <model>`, then reload.")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Button("Reload models") {
                                    Task { await loadOllamaModels() }
                                }
                            }
                        } else {
                            Picker("Ollama model", selection: $ollamaModel) {
                                ForEach(ollamaModels) { model in
                                    Text(model.name).tag(model.name)
                                }
                            }

                            Button("Reload models") {
                                Task { await loadOllamaModels() }
                            }
                        }
                    } else {
                        TextField("Gemini model", text: $geminiModel)
                            .textFieldStyle(.roundedBorder)

                        HStack(spacing: 8) {
                            if isGeminiAPIKeyVisible {
                                TextField(CloudProvider.gemini.apiKeyPlaceholder, text: $geminiAPIKey)
                            } else {
                                SecureField(CloudProvider.gemini.apiKeyPlaceholder, text: $geminiAPIKey)
                            }

                            Button {
                                isGeminiAPIKeyVisible.toggle()
                            } label: {
                                Image(systemName: isGeminiAPIKeyVisible ? "eye.slash" : "eye")
                            }
                            .buttonStyle(.borderless)
                            .help(isGeminiAPIKeyVisible ? "Hide API key" : "Show API key")
                        }
                        .textFieldStyle(.roundedBorder)

                        HStack {
                            Button("Save API key") {
                                saveGeminiAPIKey()
                            }
                            .disabled(geminiAPIKey.isEmpty)

                            if hasSavedGeminiAPIKey {
                                Text("API key saved in Keychain")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)

                                Button("Remove saved key", role: .destructive) {
                                    removeSavedGeminiAPIKey()
                                }
                            }
                        }

                        if let keychainError {
                            Text(keychainError)
                                .font(.caption)
                                .foregroundStyle(.red)
                        }
                    }
                }
                .padding(.top, 4)
            }

            if isScanning {
                ProgressView("Analyzing tracked chats…")
            }

            if let errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)
            }

            if !isScanning && plans.isEmpty {
                ContentUnavailableView(
                    "No plans from this scan",
                    systemImage: "checklist",
                    description: Text("Choose Scan chats to analyze your tracked conversations.")
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(plans) { plan in
                            PlanCard(plan: plan)
                        }
                    }
                }
            }
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .task(id: provider) {
            guard provider == .ollama else { return }
            await loadOllamaModels()
        }
        .task {
            refreshGeminiAPIKeyStatus()
        }
    }

    private func scanChats() {
        isScanning = true
        status = "Scanning tracked chats…"
        errorMessage = nil

        let selectedProvider = provider
        let selectedModel = selectedModel
        let apiKey: String?

        do {
            apiKey = try geminiAPIKeyForScan(provider: selectedProvider)
        } catch {
            status = error.localizedDescription
            errorMessage = error.localizedDescription
            isScanning = false
            return
        }

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let results = try BackendClient().scanChats(
                    provider: selectedProvider,
                    model: selectedModel,
                    apiKey: apiKey
                )
                DispatchQueue.main.async {
                    plans = results
                    status = "Analyzed \(results.count) chat\(results.count == 1 ? "" : "s")."
                    isScanning = false
                }
            } catch {
                DispatchQueue.main.async {
                    status = error.localizedDescription
                    errorMessage = error.localizedDescription
                    isScanning = false
                }
            }
        }
    }

    private var selectedModel: String {
        provider == .ollama ? ollamaModel : geminiModel
    }

    private func loadOllamaModels() async {
        isLoadingOllamaModels = true
        ollamaError = nil

        do {
            let models = try await OllamaClient().listModels()
            ollamaModels = models

            if !models.contains(where: { $0.name == ollamaModel }) {
                ollamaModel = models.first?.name ?? ""
            }
        } catch {
            ollamaModels = []
            ollamaError = error.localizedDescription
        }

        isLoadingOllamaModels = false
    }

    private func saveGeminiAPIKey() {
        do {
            try keychain.save(geminiAPIKey, for: CloudProvider.gemini.apiKeyAccount)
            geminiAPIKey = ""
            hasSavedGeminiAPIKey = true
            keychainError = nil
        } catch {
            keychainError = error.localizedDescription
        }
    }

    private func removeSavedGeminiAPIKey() {
        do {
            try keychain.delete(CloudProvider.gemini.apiKeyAccount)
            geminiAPIKey = ""
            hasSavedGeminiAPIKey = false
            keychainError = nil
        } catch {
            keychainError = error.localizedDescription
        }
    }

    private func refreshGeminiAPIKeyStatus() {
        do {
            hasSavedGeminiAPIKey = try keychain.contains(CloudProvider.gemini.apiKeyAccount)
        } catch {
            keychainError = error.localizedDescription
        }
    }

    private func geminiAPIKeyForScan(provider: ModelProvider) throws -> String? {
        guard provider == .gemini else { return nil }

        if !geminiAPIKey.isEmpty {
            try keychain.save(geminiAPIKey, for: CloudProvider.gemini.apiKeyAccount)
            geminiAPIKey = ""
            hasSavedGeminiAPIKey = true
        }

        guard let apiKey = try keychain.read(for: CloudProvider.gemini.apiKeyAccount) else {
            throw KeychainError.missingValue
        }
        return apiKey
    }
}

private struct PlanCard: View {
    let plan: Plan

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(plan.status.rawValue.uppercased())
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(statusColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor.opacity(0.15), in: Capsule())

                Spacer()

                Text(plan.chatID)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Text(plan.plan ?? "No plan identified.")
                .font(.headline)

            if let blockers = plan.blockers, !blockers.isEmpty {
                VStack(alignment: .leading, spacing: 3) {
                    Text("Blockers")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)

                    ForEach(blockers, id: \.self) { blocker in
                        Text("• \(blocker)")
                            .font(.subheadline)
                    }
                }
            }

            Text(plan.reason)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.quaternary, in: RoundedRectangle(cornerRadius: 12))
    }

    private var statusColor: Color {
        switch plan.status {
        case .active: .orange
        case .stuck: .red
        case .completed: .green
        default: .secondary
        }
    }
}

private struct ChatsView: View {
    @State private var chats: [Chat] = []
    @State private var selectedChatIDs: Set<String> = []
    @State private var savedChatIDs: Set<String> = []
    @State private var errorMessage: String?
    @State private var isLoading = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Chats")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text("Select the conversations Bruh Agent should scan.")
                .foregroundStyle(.secondary)

            if isLoading {
                ProgressView("Loading chats…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(chats) { chat in
                    Toggle(chat.chatID, isOn: selectionBinding(for: chat.chatID))
                        .toggleStyle(.checkbox)
                }
            }

            if let errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)

            }

            HStack {
                Button("Reload") {
                    loadChats()
                }

                Button("Save selection") {
                    saveSelection()
                }
                .disabled(isLoading || selectedChatIDs == savedChatIDs)

                Spacer()
            }

            Text("Showing the 10 most recently active chats.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(24)
        .task {
            loadChats()
        }
    }

    private func selectionBinding(for chatID: String) -> Binding<Bool> {
        Binding(
            get: { selectedChatIDs.contains(chatID) },
            set: { isSelected in
                if isSelected {
                    selectedChatIDs.insert(chatID)
                } else {
                    selectedChatIDs.remove(chatID)
                }
            }
        )
    }

    private func loadChats() {
        isLoading = true
        errorMessage = nil

        do {
            let client = BackendClient()
            chats = try client.listChats(limit: 10)
            savedChatIDs = Set(try client.trackedChats().map(\.chatID))
            selectedChatIDs = savedChatIDs
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    private func saveSelection() {
        isLoading = true
        errorMessage = nil

        do {
            let client = BackendClient()

            for chatID in selectedChatIDs.subtracting(savedChatIDs) {
                try client.addTrackedChat(chatID)
            }
            for chatID in savedChatIDs.subtracting(selectedChatIDs) {
                try client.removeTrackedChat(chatID)
            }

            savedChatIDs = selectedChatIDs
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }
}

#Preview {
    ContentView()
}
