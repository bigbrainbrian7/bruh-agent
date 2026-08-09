import Foundation

struct CalendarEventArguments: Decodable, Sendable {
    let title: String
    let startTime: Date
    let endTime: Date
    let location: String?
    let notes: String?

    private enum CodingKeys: String, CodingKey {
        case title, location, notes
        case startTime = "start_time"
        case endTime = "end_time"
    }
}

struct CalendarEventToolCall: Decodable, Identifiable, Sendable {
    let id: String
    let arguments: CalendarEventArguments
}

enum ToolCall: Decodable, Identifiable, Sendable {
    case createCalendarEvent(CalendarEventToolCall)

    var id: String {
        switch self {
        case .createCalendarEvent(let call): call.id
        }
    }

    private enum CodingKeys: String, CodingKey { case name }
    private enum ToolName: String, Decodable { case createCalendarEvent = "create_calendar_event" }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        switch try container.decode(ToolName.self, forKey: .name) {
        case .createCalendarEvent:
            self = .createCalendarEvent(try CalendarEventToolCall(from: decoder))
        }
    }
}

enum ToolResultStatus: String, Codable, Sendable { case completed, dismissed, failed }

struct ToolResult: Codable, Sendable {
    let toolCallID: String
    let status: ToolResultStatus
    let externalID: String?
    let summary: String

    private enum CodingKeys: String, CodingKey {
        case status, summary
        case toolCallID = "tool_call_id"
        case externalID = "external_id"
    }
}
