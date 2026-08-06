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
    @State private var plans: [PlanResult] = []
    @State private var status = "Ready to scan your tracked chats."
    @State private var errorMessage: String?
    @State private var isScanning = false

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
                .disabled(isScanning)
            }

            Text(status)
                .foregroundStyle(.secondary)

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
    }

    private func scanChats() {
        isScanning = true
        status = "Scanning tracked chats…"
        errorMessage = nil

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let results = try BackendClient().scanChats()
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
}

private struct PlanCard: View {
    let plan: PlanResult

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(plan.status.uppercased())
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
        case "active": .orange
        case "stuck": .red
        case "completed": .green
        default: .secondary
        }
    }
}

private struct ChatsView: View {
    @State private var chats: [ChatSummary] = []
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
