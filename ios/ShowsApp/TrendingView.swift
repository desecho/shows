import SwiftUI

struct TrendingView: View {
    @EnvironmentObject private var apiService: APIService

    @State private var shows: [SearchShow] = []
    @State private var isLoading = false
    @State private var hasLoadedShows = false
    @State private var errorMessage: String?
    @State private var busyShowID: Int?

    private let columns = [
        GridItem(.adaptive(minimum: 140, maximum: 170), spacing: 16, alignment: .top),
    ]

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && shows.isEmpty {
                    ProgressView("Loading trending shows...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if shows.isEmpty {
                    emptyState
                } else {
                    content
                }
            }
            .navigationTitle("Trending")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Refresh") {
                            Task {
                                await loadTrendingShows()
                            }
                        }

                        Button("Log Out", role: .destructive) {
                            apiService.logout()
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .task {
                guard !hasLoadedShows else { return }
                hasLoadedShows = true
                await loadTrendingShows()
            }
            .refreshable {
                await loadTrendingShows()
            }
            .alert("Trending Error", isPresented: Binding(
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

    private var content: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 6) {
                    Label("Hot this week", systemImage: "flame.fill")
                        .font(.headline)
                        .foregroundStyle(.orange)

                    Text("Discover the shows people are watching right now.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach(shows) { show in
                        TrendingShowTile(
                            show: show,
                            isBusy: busyShowID == show.id,
                            onAdd: { destination in
                                add(show, to: destination)
                            }
                        )
                    }
                }
            }
            .padding(16)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            ContentUnavailableView(
                "No trending shows",
                systemImage: "flame",
                description: Text(emptyStateMessage)
            )

            Button("Retry") {
                Task {
                    await loadTrendingShows()
                }
            }
            .buttonStyle(.borderedProminent)
        }
    }

    private var emptyStateMessage: String {
        if let errorMessage {
            return errorMessage
        }
        return "You're caught up for now. Pull to refresh and check back later."
    }

    private func loadTrendingShows() async {
        isLoading = true
        errorMessage = nil

        defer { isLoading = false }

        do {
            shows = try await apiService.fetchTrendingShows()
        } catch {
            errorMessage = message(for: error)
        }
    }

    private func add(_ show: SearchShow, to destination: ListType) {
        guard busyShowID == nil else { return }

        busyShowID = show.id

        Task {
            defer { busyShowID = nil }

            do {
                try await apiService.addSearchResult(show, to: destination)
                shows.removeAll { $0.id == show.id }
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

private struct TrendingShowTile: View {
    let show: SearchShow
    let isBusy: Bool
    let onAdd: (ListType) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            TrendingPosterArtwork(url: show.posterURL)
                .overlay(alignment: .topLeading) {
                    Label("Trending", systemImage: "flame.fill")
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(.orange)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 6)
                        .background(.ultraThinMaterial, in: Capsule())
                        .padding(8)
                }

            VStack(alignment: .leading, spacing: 6) {
                Text(show.title)
                    .font(.subheadline.weight(.semibold))
                    .lineLimit(2)

                if show.titleOriginal != show.title {
                    Text(show.titleOriginal)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }

                if let firstAirDate = show.firstAirDate {
                    Label(firstAirDate, systemImage: "calendar")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Label(
                    show.isReleased ? "Released" : "Upcoming",
                    systemImage: show.isReleased ? "checkmark.circle.fill" : "clock"
                )
                .font(.caption)
                .foregroundStyle(show.isReleased ? Color.secondary : Color.orange)
            }

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
                HStack(spacing: 6) {
                    if isBusy {
                        ProgressView()
                            .controlSize(.small)
                            .tint(.white)
                    } else {
                        Image(systemName: "plus.circle.fill")
                    }

                    Text(isBusy ? "Adding..." : "Add to List")
                        .font(.subheadline.weight(.semibold))
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(Color.accentColor, in: Capsule())
            }
            .disabled(isBusy)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct TrendingPosterArtwork: View {
    let url: URL?

    var body: some View {
        AsyncImage(url: url) { image in
            image
                .resizable()
                .scaledToFill()
        } placeholder: {
            RoundedRectangle(cornerRadius: 14)
                .fill(Color.gray.opacity(0.2))
                .overlay {
                    Image(systemName: "tv")
                        .foregroundStyle(.secondary)
                }
        }
        .aspectRatio(2 / 3, contentMode: .fit)
        .frame(maxWidth: .infinity)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .overlay {
            RoundedRectangle(cornerRadius: 14)
                .strokeBorder(Color.primary.opacity(0.08))
        }
        .shadow(color: .black.opacity(0.08), radius: 6, y: 2)
    }
}
