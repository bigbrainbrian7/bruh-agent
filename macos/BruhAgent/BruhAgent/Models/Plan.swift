import Foundation

enum PlanStatus: String, Codable, Sendable {
    case active
    case stuck
    case completed
    case none
}

struct PlanExtraction: Codable, Sendable {
    let status: PlanStatus
    let plan: String?
    let blockers: [String]?
    let reason: String
    let confidence: Double
}

struct Plan: Codable, Identifiable, Sendable {
    let status: PlanStatus
    let plan: String?
    let blockers: [String]?
    let reason: String
    let chatID: String
    let confidence: Double
    let updatedAt: Date?

    var id: String { chatID }

    private enum CodingKeys: String, CodingKey {
        case status, plan, blockers, reason, confidence
        case chatID = "chat_id"
        case updatedAt = "updated_at"
    }
}
