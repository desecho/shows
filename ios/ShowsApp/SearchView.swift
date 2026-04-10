import SwiftUI

struct SearchView: View {
    @EnvironmentObject private var apiService: APIService

    @State private var query = ""
    @State private var searchType: SearchType = .show
    @State private var popularOnly = true
    @State private var sortByDate = false
    @State private var results: [SearchShow] = []
    @State private var isSearching = false
    @State private var errorMessage: String?
    @State private var busyResultID: Int?
    @State private var searchTask: Task<Void, Never>?

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                controls

                Group {
                    if query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                        ContentUnavailableView(
                            "Search Shows",
                            systemImage: "magnifyingglass",
                            description: Text("Search by show title or actor.")
                        )
                    } else if isSearching && results.isEmpty {
                        ProgressView("Searching...")
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if results.isEmpty {
                        ContentUnavailableView.search(text: query)
                    } else {
                        List(results) { result in
                            DiscoverShowRow(
                                show: result,
                                isBusy: busyResultID == result.id,
                                onAdd: { destination in
                                    add(result, to: destination)
                                }
                            )
                        }
                        .listStyle(.plain)
                    }
                }
            }
            .navigationTitle("Search")
            .searchable(text: $query, prompt: "Search shows or actors")
            .onSubmit(of: .search) {
                triggerImmediateSearch()
            }
            .onChange(of: query) { _, _ in
                scheduleSearch()
            }
            .onChange(of: searchType) { _, _ in
                scheduleSearchIfPossible()
            }
            .onChange(of: popularOnly) { _, _ in
                scheduleSearchIfPossible()
            }
            .onChange(of: sortByDate) { _, _ in
                scheduleSearchIfPossible()
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Clear Results") {
                            query = ""
                            results = []
                        }

                        Button("Log Out", role: .destructive) {
                            apiService.logout()
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .alert("Search Error", isPresented: Binding(
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
        .onDisappear {
            searchTask?.cancel()
        }
    }

    private var controls: some View {
        VStack(alignment: .leading, spacing: 12) {
            Picker("Search Type", selection: $searchType) {
                ForEach(SearchType.allCases) { type in
                    Text(type.title).tag(type)
                }
            }
            .pickerStyle(.segmented)

            Toggle("Only show popular results", isOn: $popularOnly)
            Toggle("Sort by air date", isOn: $sortByDate)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
    }

    private func scheduleSearchIfPossible() {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        scheduleSearch()
    }

    private func triggerImmediateSearch() {
        searchTask?.cancel()
        searchTask = Task {
            await performSearch()
        }
    }

    private func scheduleSearch() {
        searchTask?.cancel()

        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedQuery.isEmpty else {
            results = []
            isSearching = false
            return
        }

        searchTask = Task {
            try? await Task.sleep(nanoseconds: 350_000_000)
            guard !Task.isCancelled else { return }
            await performSearch()
        }
    }

    private func performSearch() async {
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedQuery.isEmpty else {
            results = []
            return
        }

        isSearching = true
        errorMessage = nil

        do {
            results = try await apiService.searchShows(
                query: trimmedQuery,
                type: searchType,
                popularOnly: popularOnly,
                sortByDate: sortByDate
            )
        } catch {
            errorMessage = message(for: error)
        }

        isSearching = false
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

struct DiscoverShowRow: View {
    let show: SearchShow
    let isBusy: Bool
    let onAdd: (ListType) -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            PosterThumbnail(url: show.posterURL)

            VStack(alignment: .leading, spacing: 8) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(show.title)
                        .font(.headline)
                        .lineLimit(2)

                    if show.titleOriginal != show.title {
                        Text(show.titleOriginal)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                }

                HStack(spacing: 10) {
                    Label(show.isReleased ? "Released" : "Upcoming", systemImage: show.isReleased ? "checkmark.circle.fill" : "clock")

                    if let firstAirDate = show.firstAirDate {
                        Label(firstAirDate, systemImage: "calendar")
                    }
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            Spacer(minLength: 8)

            Menu {
                ForEach(ListType.allCases) { listType in
                    Button {
                        onAdd(listType)
                    } label: {
                        Label("Add to \(listType.title)", systemImage: listType.systemImage)
                    }
                    .disabled(listType == .watched && !show.isReleased)
                }
            } label: {
                if isBusy {
                    ProgressView()
                } else {
                    Image(systemName: "plus.circle.fill")
                        .font(.title3)
                }
            }
            .disabled(isBusy)
        }
        .padding(.vertical, 4)
    }
}
