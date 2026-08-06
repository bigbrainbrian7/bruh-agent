import Foundation

struct Message: Codable, Identifiable, Hashable, Sendable {
    let id: Int
    let chatID: String
    let sender: String
    let timestamp: Date
    let text: String

    private enum CodingKeys: String, CodingKey {
        case id
        case chatID = "chat_id"
        case sender, timestamp, text
    }
}
