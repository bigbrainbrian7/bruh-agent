import Foundation

private struct ChatsResponse: Decodable {
    let chats: [Chat]
}

enum ModelProvider: String, CaseIterable, Identifiable, Sendable {
    case ollama
    case gemini

    var id: Self { self }

    var displayName: String {
        switch self {
        case .ollama: "Ollama (local)"
        case .gemini: "Gemini (cloud)"
        }
    }
}

/// Describes the information the app needs for any cloud model provider.
/// Additional cloud providers can use this same shape later.
struct CloudProvider: Identifiable {
    let id: String
    let displayName: String
    let defaultModel: String
    let apiKeyEnvironmentVariable: String
    let apiKeyPlaceholder: String

    static let gemini = CloudProvider(
        id: "gemini",
        displayName: "Gemini",
        defaultModel: "gemini-3.5-flash-lite",
        apiKeyEnvironmentVariable: "GEMINI_API_KEY",
        apiKeyPlaceholder: "Paste your Gemini API key"
    )
}

private struct ScanResponse: Decodable {
    let plans: [Plan]
}

enum BackendError: LocalizedError {
    case executableNotFound
    case commandFailed(String)

    var errorDescription: String? {
        switch self {
        case .executableNotFound:
            return "Bruh's Python backend is not bundled with this app."
        case .commandFailed(let message):
            return message
        }
    }
}

struct BackendClient {
    func scanChats(
        provider: ModelProvider,
        model: String,
        apiKey: String? = nil
    ) throws -> [Plan] {
        var environment: [String: String] = [:]
        if provider == .gemini, let apiKey, !apiKey.isEmpty {
            environment[CloudProvider.gemini.apiKeyEnvironmentVariable] = apiKey
        }

        let output = try run(
            arguments: ["scan", "--json", "--provider", provider.rawValue, "--model", model],
            environment: environment
        )
        return try makeDecoder().decode(ScanResponse.self, from: output).plans
    }

    func listChats(limit: Int) throws -> [Chat] {
        let output = try run(arguments: ["chats", "list", "--limit", String(limit), "--json"])
        return try JSONDecoder().decode(ChatsResponse.self, from: output).chats
    }

    func trackedChats() throws -> [Chat] {
        let output = try run(arguments: ["chats", "tracked", "--json"])
        return try JSONDecoder().decode(ChatsResponse.self, from: output).chats
    }

    func addTrackedChat(_ chatID: String) throws {
        _ = try run(arguments: ["chats", "add", chatID])
    }

    func removeTrackedChat(_ chatID: String) throws {
        _ = try run(arguments: ["chats", "rm", chatID])
    }

    private func run(
        arguments: [String],
        environment: [String: String] = [:],
        captureOutput: Bool = true
    ) throws -> Data {
        let process = Process()
        process.executableURL = try executableURL()
        process.arguments = arguments
        process.environment = ProcessInfo.processInfo.environment.merging(environment) { _, value in value }


        let standardOutput = captureOutput ? Pipe() : nil
        let standardError = Pipe()
        process.standardOutput = standardOutput ?? FileHandle.nullDevice
        process.standardError = standardError

        try process.run()
        let output = standardOutput?.fileHandleForReading.readDataToEndOfFile() ?? Data()
        process.waitUntilExit()
        let errorData = standardError.fileHandleForReading.readDataToEndOfFile()

        guard process.terminationStatus == 0 else {
            let message = String(data: errorData, encoding: .utf8) ?? "Unknown backend error."
            throw BackendError.commandFailed(message.trimmingCharacters(in: .whitespacesAndNewlines))
        }

        return output
    }

    private func executableURL() throws -> URL {
        let fileManager = FileManager.default

        if let developmentPath = ProcessInfo.processInfo.environment["BRUH_EXECUTABLE"],
           fileManager.isExecutableFile(atPath: developmentPath) {
            return URL(fileURLWithPath: developmentPath)
        }

        if let bundledURL = Bundle.main.url(
            forResource: "bruh",
            withExtension: nil,
            subdirectory: "backend"
        ), fileManager.isExecutableFile(atPath: bundledURL.path) {
            return bundledURL
        }

        throw BackendError.executableNotFound
    }

    # not validated after gpted. just gotta hope it works
    private func makeDecoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let timestamp = try container.decode(String.self)

            let fractionalFormatter = ISO8601DateFormatter()
            fractionalFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

            let standardFormatter = ISO8601DateFormatter()
            standardFormatter.formatOptions = [.withInternetDateTime]

            if let date = fractionalFormatter.date(from: timestamp)
                ?? standardFormatter.date(from: timestamp) {
                return date
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Expected an ISO-8601 timestamp."
            )
        }
        return decoder
    }
}
