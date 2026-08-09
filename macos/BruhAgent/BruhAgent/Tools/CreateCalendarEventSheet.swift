import SwiftUI

struct CreateCalendarEventSheet: View {
    let onComplete: (ToolResult) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var draft: CalendarEventDraft
    @State private var isSaving = false
    @State private var errorMessage: String?

    init(draft: CalendarEventDraft, onComplete: @escaping (ToolResult) -> Void) {
        _draft = State(initialValue: draft)
        self.onComplete = onComplete
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Add to Calendar").font(.title2).fontWeight(.semibold)
            Form {
                TextField("Title", text: $draft.title)
                DatePicker("Starts", selection: $draft.startTime)
                DatePicker("Ends", selection: $draft.endTime)
                TextField("Location", text: $draft.location)
                TextField("Notes", text: $draft.notes, axis: .vertical).lineLimit(2...4)
            }
            if let errorMessage {
                Text(errorMessage).font(.caption).foregroundStyle(.red)
            }
            HStack {
                Button("Cancel") { dismiss() }
                Spacer()
                Button("Add Event") { addEvent() }
                    .buttonStyle(.borderedProminent)
                    .disabled(isSaving || draft.title.isEmpty || draft.endTime <= draft.startTime)
            }
        }
        .padding(24)
        .frame(width: 440)
    }

    private func addEvent() {
        isSaving = true
        errorMessage = nil
        Task {
            do {
                let result = try await ToolRegistry().executeCalendar(draft)
                onComplete(result)
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
            }
            isSaving = false
        }
    }
}
