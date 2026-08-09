import EventKit
import Foundation

struct CalendarEventDraft: Identifiable {
    let id: String
    var title: String
    var startTime: Date
    var endTime: Date
    var location: String
    var notes: String
}

enum CalendarToolError: LocalizedError {
    case invalidArguments, invalidTimeRange, accessDenied, noWritableCalendar

    var errorDescription: String? {
        switch self {
        case .invalidArguments: "The calendar proposal has invalid details."
        case .invalidTimeRange: "The event must end after it starts."
        case .accessDenied: "Calendar access was not granted."
        case .noWritableCalendar: "No writable calendar is available."
        }
    }
}

struct CalendarTool {
    func makeDraft(from call: ToolCall) throws -> CalendarEventDraft {
        let arguments: CalendarEventArguments
        switch call {
        case .createCalendarEvent(let calendarCall):
            arguments = calendarCall.arguments
        }
        guard arguments.endTime > arguments.startTime else { throw CalendarToolError.invalidTimeRange }

        return CalendarEventDraft(
            id: call.id,
            title: arguments.title,
            startTime: arguments.startTime,
            endTime: arguments.endTime,
            location: arguments.location ?? "",
            notes: arguments.notes ?? ""
        )
    }

    func execute(_ draft: CalendarEventDraft) async throws -> ToolResult {
        guard draft.endTime > draft.startTime else { throw CalendarToolError.invalidTimeRange }
        let eventStore = EKEventStore()
        let granted = try await eventStore.requestWriteOnlyAccessToEvents()
        guard granted else { throw CalendarToolError.accessDenied }
        guard let calendar = eventStore.defaultCalendarForNewEvents else {
            throw CalendarToolError.noWritableCalendar
        }

        let event = EKEvent(eventStore: eventStore)
        event.title = draft.title
        event.startDate = draft.startTime
        event.endDate = draft.endTime
        event.location = draft.location.isEmpty ? nil : draft.location
        event.notes = draft.notes.isEmpty ? nil : draft.notes
        event.calendar = calendar
        try eventStore.save(event, span: .thisEvent)

        return ToolResult(toolCallID: draft.id, status: .completed, externalID: event.eventIdentifier, summary: "Added \(draft.title) to Calendar.")
    }
}

struct ToolRegistry {
    private let calendarTool = CalendarTool()

    func calendarDraft(for call: ToolCall) throws -> CalendarEventDraft {
        try calendarTool.makeDraft(from: call)
    }

    func executeCalendar(_ draft: CalendarEventDraft) async throws -> ToolResult {
        try await calendarTool.execute(draft)
    }
}
