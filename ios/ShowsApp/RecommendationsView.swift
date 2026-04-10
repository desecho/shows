import SwiftUI

struct RecommendationsView: View {
    @EnvironmentObject private var apiService: APIService

    @State private var preferences = RecommendationPreferences()
    @State private var results: [SearchShow] = []
    @State private var isLoading = false
    @State private var hasSearched = false
    @State private var errorMessage: String?
    @State private var busyResultID: Int?

    var body: some View {
        NavigationStack {
            List {
                Section("Preferences") {
                    Picker("Preferred Genre", selection: $preferences.preferredGenre) {
                        Text("Any Genre").tag(nil as ShowGenre?)
                        ForEach(ShowGenre.allCases) { genre in
                            Text(genre.rawValue).tag(Optional(genre))
                        }
                    }

                    Picker("Minimum Rating", selection: $preferences.minRating) {
                        Text("Any").tag(0)
                        ForEach(1 ... AIRecommendationConstants.maxRating, id: \.self) { rating in
                            Text("\(rating)+").tag(rating)
                        }
                    }

                    Stepper(
                        "Recommendations: \(preferences.recommendationsNumber)",
                        value: $preferences.recommendationsNumber,
                        in: AIRecommendationConstants.minRecommendations ... AIRecommendationConstants.maxRecommendations
                    )

                    Stepper(
                        "Start Year: \(preferences.yearStart)",
                        value: $preferences.yearStart,
                        in: AIRecommendationConstants.minYear ... preferences.yearEnd
                    )

                    Stepper(
                        "End Year: \(preferences.yearEnd)",
                        value: $preferences.yearEnd,
                        in: preferences.yearStart ... AIRecommendationConstants.currentYear
                    )
                }

                Section {
                    Button {
                        Task {
                            await loadRecommendations()
                        }
                    } label: {
                        HStack {
                            Spacer()
                            if isLoading {
                                ProgressView()
                            } else {
                                Text("Get AI Recommendations")
                                    .fontWeight(.semibold)
                            }
                            Spacer()
                        }
                    }
                    .disabled(isLoading)
                }

                if !results.isEmpty {
                    Section("Recommendations") {
                        ForEach(results) { result in
                            DiscoverShowRow(
                                show: result,
                                isBusy: busyResultID == result.id,
                                onAdd: { destination in
                                    add(result, to: destination)
                                }
                            )
                        }
                    }
                } else if isLoading {
                    Section {
                        VStack(spacing: 12) {
                            ProgressView()
                            Text("Generating recommendations...")
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                    }
                } else if hasSearched {
                    Section {
                        ContentUnavailableView(
                            "No Recommendations Found",
                            systemImage: "sparkles.tv",
                            description: Text("Try broadening the year range or lowering the minimum rating.")
                        )
                    }
                } else {
                    Section {
                        ContentUnavailableView(
                            "AI Recommendations",
                            systemImage: "sparkles",
                            description: Text("Use your watched history plus the filters above to discover your next show.")
                        )
                    }
                }
            }
            .navigationTitle("AI")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Log Out", role: .destructive) {
                            apiService.logout()
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .alert("Recommendations Error", isPresented: Binding(
                get: { errorMessage != nil },
                set: { isPresented in
                    if !isPresented {
                        errorMessage = nil
                    }
                }
            )) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage ?? "")
            }
        }
    }

    private func loadRecommendations() async {
        isLoading = true
        hasSearched = true
        errorMessage = nil

        defer { isLoading = false }

        do {
            results = try await apiService.fetchRecommendations(preferences: preferences)
        } catch {
            results = []
            errorMessage = message(for: error)
        }
    }

    private func add(_ show: SearchShow, to destination: ListType) {
        guard busyResultID == nil else { return }

        busyResultID = show.id
        Task {
            defer { busyResultID = nil }
            do {
                try await apiService.addSearchResult(show, to: destination)
                results.removeAll { $0.id == show.id }
            } catch {
                errorMessage = message(for: error)
            }
        }
    }

    private func message(for error: Error) -> String {
        if let apiError = error as? APIError {
            return apiError.localizedDescription
        }
        return error.localizedDescription
    }
}
