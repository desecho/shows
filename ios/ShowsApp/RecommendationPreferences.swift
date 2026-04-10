import Foundation

struct AIRecommendationConstants {
    static let maxRecommendations = 50
    static let minRecommendations = 1
    static let minRating = 0
    static let maxRating = 5
    static let minYear = 1920
    static let currentYear = Calendar.current.component(.year, from: Date())
}

enum ShowGenre: String, CaseIterable, Identifiable {
    case actionAdventure = "Action & Adventure"
    case animation = "Animation"
    case comedy = "Comedy"
    case crime = "Crime"
    case documentary = "Documentary"
    case drama = "Drama"
    case family = "Family"
    case kids = "Kids"
    case mystery = "Mystery"
    case news = "News"
    case reality = "Reality"
    case sciFiFantasy = "Sci-Fi & Fantasy"
    case soap = "Soap"
    case talk = "Talk"
    case warPolitics = "War & Politics"
    case western = "Western"

    var id: String { rawValue }
}

struct RecommendationPreferences: Equatable {
    var preferredGenre: ShowGenre?
    var yearStart: Int
    var yearEnd: Int
    var minRating: Int
    var recommendationsNumber: Int

    init() {
        self.preferredGenre = nil
        self.yearStart = 2000
        self.yearEnd = AIRecommendationConstants.currentYear
        self.minRating = AIRecommendationConstants.minRating
        self.recommendationsNumber = AIRecommendationConstants.maxRecommendations
    }

    var queryItems: [URLQueryItem] {
        var items: [URLQueryItem] = [
            URLQueryItem(name: "yearStart", value: String(yearStart)),
            URLQueryItem(name: "yearEnd", value: String(yearEnd)),
            URLQueryItem(name: "recommendationsNumber", value: String(recommendationsNumber)),
        ]

        if let preferredGenre {
            items.append(URLQueryItem(name: "preferredGenre", value: preferredGenre.rawValue))
        }

        if minRating > AIRecommendationConstants.minRating {
            items.append(URLQueryItem(name: "minRating", value: String(minRating)))
        }

        return items
    }
}
