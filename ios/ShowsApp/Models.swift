import Foundation

struct LoginRequest: Encodable {
    let username: String
    let password: String
}

struct LoginResponse: Decodable {
    let access: String
    let refresh: String
}

struct RefreshRequest: Encodable {
    let refresh: String
}

struct RefreshResponse: Decodable {
    let access: String
}

struct SearchOptionsPayload: Encodable {
    let popularOnly: Bool
    let sortByDate: Bool
}

struct AddFromSearchRequest: Encodable {
    let showId: Int
    let listId: Int
}

struct ListUpdateRequest: Encodable {
    let listId: Int
}

struct RecordOrderUpdate: Encodable {
    let id: Int
    let order: Int
}

struct SaveRecordOrderRequest: Encodable {
    let records: [RecordOrderUpdate]
}

struct RatingUpdateRequest: Encodable {
    let rating: Int
}

struct Trailer: Codable, Equatable {
    let url: String
    let name: String
}

struct SearchShow: Codable, Identifiable, Equatable, Hashable {
    let id: Int
    let tmdbLink: String
    let firstAirDate: String?
    let title: String
    let titleOriginal: String
    let poster: String?
    let poster2x: String?
    let isReleased: Bool

    var posterURL: URL? {
        URL(string: poster ?? poster2x ?? "")
    }
}

struct Show: Codable, Identifiable, Equatable {
    let id: Int
    let title: String
    let titleOriginal: String
    let posterSmall: String?
    let posterNormal: String?
    let posterBig: String?
    let isReleased: Bool
    let imdbRating: Double?
    let firstAirDate: String?
    let firstAirDateTimestamp: Double
    let country: String?
    let writer: String?
    let genre: String?
    let actors: String?
    let overview: String?
    let status: String?
    let homepage: String?
    let imdbUrl: String
    let tmdbUrl: String
    let trailers: [Trailer]
    let hasPoster: Bool

    var posterURL: URL? {
        URL(string: posterNormal ?? posterSmall ?? posterBig ?? "")
    }
}

struct Provider: Codable, Equatable {
    let logo: String
    let name: String
}

struct ProviderRecord: Codable, Equatable {
    let tmdbWatchUrl: String
    let provider: Provider
}

struct Record: Codable, Identifiable, Equatable {
    let id: Int
    let order: Int
    let show: Show
    let comment: String
    let commentArea: Bool
    let rating: Int
    let providerRecords: [ProviderRecord]
    let listId: Int?
    let additionDate: Double

    var listType: ListType? {
        guard let listId else { return nil }
        return ListType(rawValue: listId)
    }

    func updating(order: Int) -> Record {
        Record(
            id: id,
            order: order,
            show: show,
            comment: comment,
            commentArea: commentArea,
            rating: rating,
            providerRecords: providerRecords,
            listId: listId,
            additionDate: additionDate
        )
    }
}

enum SearchType: String, CaseIterable, Identifiable {
    case show
    case actor

    var id: String { rawValue }

    var title: String {
        switch self {
        case .show:
            return "Shows"
        case .actor:
            return "Actors"
        }
    }
}

enum ListType: Int, CaseIterable, Identifiable {
    case watched = 1
    case watching = 2
    case toWatch = 3

    var id: Int { rawValue }

    var title: String {
        switch self {
        case .watched:
            return "Watched"
        case .watching:
            return "Watching"
        case .toWatch:
            return "To Watch"
        }
    }

    var systemImage: String {
        switch self {
        case .watched:
            return "eye.fill"
        case .watching:
            return "play.circle.fill"
        case .toWatch:
            return "bookmark.fill"
        }
    }

    var emptyStateSymbol: String {
        switch self {
        case .watched:
            return "eye.slash"
        case .watching:
            return "play.slash"
        case .toWatch:
            return "bookmark.slash"
        }
    }
}

enum APIError: Error, LocalizedError {
    case unauthorized
    case invalidURL
    case invalidResponse
    case decoding
    case server(String)
    case network(String)

    var errorDescription: String? {
        switch self {
        case .unauthorized:
            return "Your session has expired. Please log in again."
        case .invalidURL:
            return "The app generated an invalid request."
        case .invalidResponse:
            return "The server returned an invalid response."
        case .decoding:
            return "Failed to process the server response."
        case .server(let message):
            return message
        case .network(let message):
            return message
        }
    }
}
