import Foundation

struct Chat: Codable, Identifiable, Hashable, Sendable {
    let chatID: String
    let lastProcessedMessageID: Int
    let displayName: String?
    let participantHandles: [String]

    var id: String { chatID }

    private enum CodingKeys: String, CodingKey {
        case chatID = "chat_id"
        case lastProcessedMessageID = "last_processed_message_id"
        case displayName = "display_name"
        case participantHandles = "participant_handles"
    }
}
