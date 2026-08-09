import Contacts
import Foundation

struct ChatDisplayNameResolver {
    func resolve(_ chats: [Chat]) async -> [Chat] {
        let store = CNContactStore()
        guard await hasAccess(to: store) else { return chats }

        let namesByHandle = contactNames(from: store)
        return chats.map { chat in
            guard chat.displayName?.isEmpty != false else { return chat }

            let names = chat.participantHandles.compactMap {
                namesByHandle[normalizedHandle($0)]
            }
            let uniqueNames = Array(NSOrderedSet(array: names)) as? [String] ?? names
            guard !uniqueNames.isEmpty else { return chat }

            return Chat(
                chatID: chat.chatID,
                lastProcessedMessageID: chat.lastProcessedMessageID,
                displayName: uniqueNames.joined(separator: ", "),
                participantHandles: chat.participantHandles
            )
        }
    }

    private func hasAccess(to store: CNContactStore) async -> Bool {
        switch CNContactStore.authorizationStatus(for: .contacts) {
        case .authorized:
            return true
        case .notDetermined:
            return (try? await store.requestAccess(for: .contacts)) ?? false
        default:
            return false
        }
    }

    private func contactNames(from store: CNContactStore) -> [String: String] {
        let keys: [CNKeyDescriptor] = [
            CNContactGivenNameKey as CNKeyDescriptor,
            CNContactFamilyNameKey as CNKeyDescriptor,
            CNContactNicknameKey as CNKeyDescriptor,
            CNContactPhoneNumbersKey as CNKeyDescriptor,
            CNContactEmailAddressesKey as CNKeyDescriptor,
        ]
        let request = CNContactFetchRequest(keysToFetch: keys)
        var namesByHandle: [String: String] = [:]

        try? store.enumerateContacts(with: request) { contact, _ in
            guard let name = displayName(for: contact) else { return }

            for phone in contact.phoneNumbers {
                namesByHandle[normalizedHandle(phone.value.stringValue)] = name
            }
            for email in contact.emailAddresses {
                namesByHandle[normalizedHandle(email.value as String)] = name
            }
        }

        return namesByHandle
    }

    private func displayName(for contact: CNContact) -> String? {
        if !contact.nickname.isEmpty {
            return contact.nickname
        }

        let name = [contact.givenName, contact.familyName]
            .filter { !$0.isEmpty }
            .joined(separator: " ")
        return name.isEmpty ? nil : name
    }

    private func normalizedHandle(_ handle: String) -> String {
        let value = handle.hasPrefix("E:") ? String(handle.dropFirst(2)) : handle
        if value.contains("@") {
            return value.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        }
        return value.filter(\.isNumber)
    }
}
