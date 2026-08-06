import Foundation

struct OllamaModel: Decodable, Identifiable, Hashable, Sendable {
    let name: String

    var id: String { name }
}

private struct OllamaModelsResponse: Decodable {
    let models: [OllamaModel]
}

enum OllamaServiceError: LocalizedError {
    case unavailable
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .unavailable:
            return "Ollama is not running at localhost:11434."
        case .invalidResponse:
            return "Ollama returned an unexpected response."
        }
    }
}

struct OllamaClient {
    private let tagsURL = URL(string: "http://localhost:11434/api/tags")!

    func listModels() async throws -> [OllamaModel] {
        do {
            let (data, response) = try await URLSession.shared.data(from: tagsURL)
            guard let response = response as? HTTPURLResponse,
                  (200..<300).contains(response.statusCode) else {
                throw OllamaServiceError.invalidResponse
            }

            return try JSONDecoder().decode(OllamaModelsResponse.self, from: data).models
        } catch let error as OllamaServiceError {
            throw error
        } catch is URLError {
            throw OllamaServiceError.unavailable
        } catch {
            throw OllamaServiceError.invalidResponse
        }
    }
}
