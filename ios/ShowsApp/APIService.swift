import Combine
import Foundation

@MainActor
final class APIService: ObservableObject {
    @Published private(set) var isAuthenticated: Bool
    @Published private(set) var isRecordsLoading = false
    @Published private(set) var hasLoadedRecords = false
    @Published private(set) var recordsByList: [ListType: [Record]]
    @Published var authErrorMessage: String?

    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()
    private let cacheLifetime: TimeInterval = 300

    private let accessTokenKey = "shows_ios_access_token"
    private let refreshTokenKey = "shows_ios_refresh_token"

    private var lastRecordsRefresh: Date?

    private let baseURL: URL = {
        #if DEBUG
        return URL(string: "http://127.0.0.1:8000")!
        #else
        return URL(string: "https://api.shows.samarchyan.me")!
        #endif
    }()

    init() {
        self.isAuthenticated = UserDefaults.standard.string(forKey: accessTokenKey) != nil
        self.recordsByList = Self.emptyRecordBuckets()
    }

    func clearAuthError() {
        authErrorMessage = nil
    }

    func login(username: String, password: String) async -> Bool {
        authErrorMessage = nil

        do {
            let requestBody = try encoder.encode(LoginRequest(username: username, password: password))
            let request = try buildRequest(
                path: "token/",
                method: "POST",
                body: requestBody,
                requiresAuth: false
            )
            let response: LoginResponse = try await send(request, decodeTo: LoginResponse.self, allowTokenRefresh: false)
            store(accessToken: response.access, refreshToken: response.refresh)
            isAuthenticated = true
            try await refreshRecords(force: true)
            return true
        } catch {
            authErrorMessage = errorMessage(from: error)
            return false
        }
    }

    func logout() {
        authErrorMessage = nil
        clearSession()
    }

    func records(for listType: ListType) -> [Record] {
        recordsByList[listType] ?? []
    }

    func refreshRecords(force: Bool) async throws {
        guard isAuthenticated else {
            throw APIError.unauthorized
        }

        if !force,
           hasLoadedRecords,
           let lastRecordsRefresh,
           Date().timeIntervalSince(lastRecordsRefresh) < cacheLifetime {
            return
        }

        isRecordsLoading = true
        defer { isRecordsLoading = false }

        let request = try buildRequest(path: "records/", requiresAuth: true)
        let records: [Record] = try await send(request, decodeTo: [Record].self)

        var buckets = Self.emptyRecordBuckets()
        for record in records {
            guard let listType = record.listType else { continue }
            buckets[listType, default: []].append(record)
        }

        recordsByList = buckets
        hasLoadedRecords = true
        lastRecordsRefresh = Date()
    }

    func removeRecord(_ record: Record) async throws {
        let request = try buildRequest(
            path: "remove-record/\(record.id)/",
            method: "DELETE",
            requiresAuth: true
        )
        try await sendWithoutResponseBody(request)
        try await refreshRecords(force: true)
    }

    func moveRecord(_ record: Record, to listType: ListType) async throws {
        let body = try encoder.encode(ListUpdateRequest(listId: listType.rawValue))
        let request = try buildRequest(
            path: "add-to-list/\(record.show.id)/",
            method: "POST",
            body: body,
            requiresAuth: true
        )
        try await sendWithoutResponseBody(request)
        try await refreshRecords(force: true)
    }

    func saveRecordOrder(_ orderedRecords: [RecordOrderUpdate], for listType: ListType) async throws {
        let body = try encoder.encode(SaveRecordOrderRequest(records: orderedRecords))
        let request = try buildRequest(
            path: "save-records-order/",
            method: "PUT",
            body: body,
            requiresAuth: true
        )
        try await sendWithoutResponseBody(request)
        applyRecordOrder(orderedRecords, to: listType)
        lastRecordsRefresh = Date()
    }

    func updateRecordRating(recordId: Int, rating: Int) async throws {
        let body = try encoder.encode(RatingUpdateRequest(rating: rating))
        let request = try buildRequest(
            path: "change-rating/\(recordId)/",
            method: "PUT",
            body: body,
            requiresAuth: true
        )
        try await sendWithoutResponseBody(request)
        try await refreshRecords(force: true)
    }

    func searchShows(
        query: String,
        type: SearchType,
        popularOnly: Bool,
        sortByDate: Bool
    ) async throws -> [SearchShow] {
        let options = SearchOptionsPayload(popularOnly: popularOnly, sortByDate: sortByDate)
        let optionsData = try encoder.encode(options)
        guard let optionsJSONString = String(data: optionsData, encoding: .utf8) else {
            throw APIError.invalidResponse
        }

        let queryItems = [
            URLQueryItem(name: "query", value: query),
            URLQueryItem(name: "type", value: type.rawValue),
            URLQueryItem(name: "options", value: optionsJSONString),
        ]

        let request = try buildRequest(
            path: "search/",
            queryItems: queryItems,
            requiresAuth: false,
            includeAuthIfAvailable: true
        )
        return try await send(request, decodeTo: [SearchShow].self)
    }

    func addSearchResult(_ show: SearchShow, to listType: ListType) async throws {
        let body = try encoder.encode(AddFromSearchRequest(showId: show.id, listId: listType.rawValue))
        let request = try buildRequest(
            path: "add-to-list-from-db/",
            method: "POST",
            body: body,
            requiresAuth: true
        )
        try await sendWithoutResponseBody(request)
        try await refreshRecords(force: true)
    }

    func fetchTrendingShows() async throws -> [SearchShow] {
        let request = try buildRequest(
            path: "trending/",
            requiresAuth: false,
            includeAuthIfAvailable: true
        )
        return try await send(request, decodeTo: [SearchShow].self)
    }

    func fetchRecommendations(preferences: RecommendationPreferences) async throws -> [SearchShow] {
        let request = try buildRequest(
            path: "recommendations/",
            queryItems: preferences.queryItems,
            requiresAuth: true
        )
        return try await send(request, decodeTo: [SearchShow].self)
    }

    private func buildRequest(
        path: String,
        method: String = "GET",
        queryItems: [URLQueryItem] = [],
        body: Data? = nil,
        requiresAuth: Bool,
        includeAuthIfAvailable: Bool = false
    ) throws -> URLRequest {
        guard var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false) else {
            throw APIError.invalidURL
        }
        components.queryItems = queryItems.isEmpty ? nil : queryItems

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method

        if let body {
            request.httpBody = body
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }

        if requiresAuth {
            guard let accessToken = storedAccessToken else {
                expireSession()
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        } else if includeAuthIfAvailable, let accessToken = storedAccessToken {
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        }

        return request
    }

    private func send<T: Decodable>(
        _ request: URLRequest,
        decodeTo type: T.Type,
        allowTokenRefresh: Bool = true
    ) async throws -> T {
        let data = try await perform(request, allowTokenRefresh: allowTokenRefresh)

        do {
            return try decoder.decode(type, from: data)
        } catch {
            throw APIError.decoding
        }
    }

    private func sendWithoutResponseBody(
        _ request: URLRequest,
        allowTokenRefresh: Bool = true
    ) async throws {
        _ = try await perform(request, allowTokenRefresh: allowTokenRefresh)
    }

    private func perform(_ request: URLRequest, allowTokenRefresh: Bool) async throws -> Data {
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            switch httpResponse.statusCode {
            case 200 ... 299:
                return data
            case 401:
                if allowTokenRefresh, request.value(forHTTPHeaderField: "Authorization") != nil {
                    do {
                        try await refreshAccessToken()
                        var retriedRequest = request
                        if let refreshedAccessToken = storedAccessToken {
                            retriedRequest.setValue("Bearer \(refreshedAccessToken)", forHTTPHeaderField: "Authorization")
                        }
                        return try await perform(retriedRequest, allowTokenRefresh: false)
                    } catch {
                        expireSession()
                        throw APIError.unauthorized
                    }
                }

                if request.value(forHTTPHeaderField: "Authorization") != nil {
                    expireSession()
                    throw APIError.unauthorized
                }

                throw apiError(from: data, statusCode: httpResponse.statusCode)
            default:
                throw apiError(from: data, statusCode: httpResponse.statusCode)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.network("Network connection error. Please check your internet connection.")
        }
    }

    private func refreshAccessToken() async throws {
        guard let refreshToken = storedRefreshToken else {
            throw APIError.unauthorized
        }

        let body = try encoder.encode(RefreshRequest(refresh: refreshToken))
        let request = try buildRequest(
            path: "token/refresh/",
            method: "POST",
            body: body,
            requiresAuth: false
        )
        let response: RefreshResponse = try await send(request, decodeTo: RefreshResponse.self, allowTokenRefresh: false)
        store(accessToken: response.access, refreshToken: refreshToken)
    }

    private func apiError(from data: Data, statusCode: Int) -> APIError {
        let message = extractMessage(from: data)

        if statusCode == 404 {
            return .server(message.isEmpty ? "The requested resource was not found." : message)
        }

        if statusCode >= 500 {
            return .server(message.isEmpty ? "The server failed to complete the request." : message)
        }

        return .server(message.isEmpty ? "The request failed with status \(statusCode)." : message)
    }

    private func extractMessage(from data: Data) -> String {
        guard !data.isEmpty else { return "" }

        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            if let status = json["status"] as? String {
                switch status {
                case "unreleased":
                    return "This show has not been released yet, so it cannot be added to Watched."
                case "not_found":
                    return "The selected show could not be loaded from the backend."
                default:
                    return status
                }
            }

            if let detail = json["detail"] as? String {
                return detail
            }

            if let error = json["error"] as? String {
                return error
            }

            for value in json.values {
                if let messages = value as? [String], let first = messages.first {
                    return first
                }
                if let message = value as? String {
                    return message
                }
            }
        }

        if let string = String(data: data, encoding: .utf8) {
            return string
        }

        return ""
    }

    private func errorMessage(from error: Error) -> String {
        if let apiError = error as? APIError, let description = apiError.errorDescription {
            return description
        }

        return error.localizedDescription
    }

    private func store(accessToken: String, refreshToken: String) {
        UserDefaults.standard.set(accessToken, forKey: accessTokenKey)
        UserDefaults.standard.set(refreshToken, forKey: refreshTokenKey)
    }

    private func applyRecordOrder(_ orderedRecords: [RecordOrderUpdate], to listType: ListType) {
        guard var records = recordsByList[listType], !records.isEmpty else {
            return
        }

        let orderByID = Dictionary(uniqueKeysWithValues: orderedRecords.map { ($0.id, $0.order) })
        records = records
            .map { record in
                guard let updatedOrder = orderByID[record.id] else {
                    return record
                }
                return record.updating(order: updatedOrder)
            }
            .sorted { lhs, rhs in
                if lhs.order == rhs.order {
                    return lhs.additionDate > rhs.additionDate
                }
                return lhs.order < rhs.order
            }

        recordsByList[listType] = records
    }

    private func clearSession() {
        UserDefaults.standard.removeObject(forKey: accessTokenKey)
        UserDefaults.standard.removeObject(forKey: refreshTokenKey)
        isAuthenticated = false
        hasLoadedRecords = false
        lastRecordsRefresh = nil
        recordsByList = Self.emptyRecordBuckets()
    }

    private func expireSession() {
        clearSession()
        authErrorMessage = APIError.unauthorized.errorDescription
    }

    private var storedAccessToken: String? {
        UserDefaults.standard.string(forKey: accessTokenKey)
    }

    private var storedRefreshToken: String? {
        UserDefaults.standard.string(forKey: refreshTokenKey)
    }

    private static func emptyRecordBuckets() -> [ListType: [Record]] {
        var buckets: [ListType: [Record]] = [:]
        for listType in ListType.allCases {
            buckets[listType] = []
        }
        return buckets
    }
}
