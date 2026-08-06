import Foundation

struct ChatSummary: Decodable, Identifiable, Hashable {
    let chatID: String

    var id: String { chatID }

    private enum CodingKeys: String, CodingKey {
        case chatID = "chat_id"
    }
}

private struct ChatsResponse: Decodable {
    let chats: [ChatSummary]
}

struct PlanResult: Decodable, Identifiable, Sendable {
    let chatID: String
    let status: String
    let plan: String?
    let blockers: [String]?
    let reason: String

    var id: String { chatID }

    private enum CodingKeys: String, CodingKey {
        case chatID = "chat_id"
        case status, plan, blockers, reason
    }
}

private struct ScanResponse: Decodable {
    let plans: [PlanResult]
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
    func scanChats() throws -> [PlanResult] {
        let output = try run(arguments: ["scan", "--json"])
        return try JSONDecoder().decode(ScanResponse.self, from: output).plans
    }

    func listChats(limit: Int) throws -> [ChatSummary] {
        let output = try run(arguments: ["chats", "list", "--limit", String(limit), "--json"])
        return try JSONDecoder().decode(ChatsResponse.self, from: output).chats
    }

    func trackedChats() throws -> [ChatSummary] {
        let output = try run(arguments: ["chats", "tracked", "--json"])
        return try JSONDecoder().decode(ChatsResponse.self, from: output).chats
    }

    func addTrackedChat(_ chatID: String) throws {
        _ = try run(arguments: ["chats", "add", chatID])
    }

    func removeTrackedChat(_ chatID: String) throws {
        _ = try run(arguments: ["chats", "rm", chatID])
    }

    private func run(arguments: [String], captureOutput: Bool = true) throws -> Data {
        let process = Process()
        process.executableURL = try executableURL()
        process.arguments = arguments


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
}
