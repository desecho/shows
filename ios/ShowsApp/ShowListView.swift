import SwiftUI

private enum ShowListSortOption: String, CaseIterable, Identifiable {
    case additionDate
    case releaseDate
    case rating
    case custom

    var id: String { rawValue }

    var title: String {
        switch self {
        case .additionDate:
            return "Date added"
        case .releaseDate:
            return "First air date"
        case .rating:
            return "Rating"
        case .custom:
            return "Custom"
        }
    }

    var systemImage: String {
        switch self {
        case .additionDate:
            return "calendar.badge.plus"
        case .releaseDate:
            return "calendar"
        case .rating:
            return "star.fill"
        case .custom:
            return "arrow.up.arrow.down"
        }
    }
}

private enum ShowListViewMode: String {
    case list
    case gallery

    var systemImage: String {
        switch self {
        case .list:
            return "list.bullet"
        case .gallery:
            return "square.grid.2x2"
        }
    }

    var accessibilityLabel: String {
        switch self {
        case .list:
            return "Show list view"
        case .gallery:
            return "Show gallery view"
        }
    }
}

struct ShowListView: View {
    let listType: ListType

    @EnvironmentObject private var apiService: APIService

    @State private var query = ""
    @State private var records: [Record] = []
    @State private var errorMessage: String?
    @State private var busyRecordID: Int?
    @State private var currentSort: ShowListSortOption = .additionDate
    @State private var currentViewMode: ShowListViewMode = .list
    @State private var isSavingCustomOrder = false

    private var sourceRecords: [Record] {
        apiService.records(for: listType)
    }

    private var availableSortOptions: [ShowListSortOption] {
        if listType == .toWatch {
            return ShowListSortOption.allCases
        }
        return ShowListSortOption.allCases.filter { $0 != .custom }
    }

    private var isCustomSortEnabled: Bool {
        listType == .toWatch && currentSort == .custom
    }

    private var alternateViewMode: ShowListViewMode {
        currentViewMode == .list ? .gallery : .list
    }

    private var galleryColumns: [GridItem] {
        [GridItem(.adaptive(minimum: 120, maximum: 160), spacing: 12, alignment: .top)]
    }

    private var filteredRecords: [Record] {
        let trimmedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines)

        guard !trimmedQuery.isEmpty else {
            return records
        }

        let normalizedQuery = trimmedQuery.lowercased()
        return records.filter { record in
            let fields = [
                record.show.title,
                record.show.titleOriginal,
                record.show.writer ?? "",
                record.show.genre ?? "",
                record.show.actors ?? "",
                record.show.overview ?? "",
                record.comment,
            ]

            return fields.contains { $0.lowercased().contains(normalizedQuery) }
        }
    }

    private var displayedRecords: [Record] {
        switch currentSort {
        case .additionDate:
            return filteredRecords.sorted { lhs, rhs in
                if lhs.additionDate == rhs.additionDate {
                    return lhs.order < rhs.order
                }
                return lhs.additionDate > rhs.additionDate
            }
        case .releaseDate:
            return filteredRecords.sorted { lhs, rhs in
                if lhs.show.firstAirDateTimestamp == rhs.show.firstAirDateTimestamp {
                    return lhs.additionDate > rhs.additionDate
                }
                return lhs.show.firstAirDateTimestamp > rhs.show.firstAirDateTimestamp
            }
        case .rating:
            return filteredRecords.sorted { lhs, rhs in
                let lhsRating = ratingValue(for: lhs)
                let rhsRating = ratingValue(for: rhs)
                if lhsRating == rhsRating {
                    return lhs.additionDate > rhs.additionDate
                }
                return lhsRating > rhsRating
            }
        case .custom:
            return filteredRecords.sorted(by: customOrderComparator)
        }
    }

    var body: some View {
        NavigationStack {
            Group {
                if apiService.isRecordsLoading && !apiService.hasLoadedRecords {
                    ProgressView("Loading shows...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if displayedRecords.isEmpty {
                    emptyState
                } else if currentViewMode == .gallery {
                    galleryContent
                } else {
                    listContent
                }
            }
            .navigationTitle(listType.title)
            .searchable(text: $query, prompt: "Filter \(listType.title.lowercased())")
            .toolbar {
                ToolbarItemGroup(placement: .topBarLeading) {
                    Menu {
                        ForEach(availableSortOptions) { option in
                            Button {
                                currentSort = option
                            } label: {
                                if currentSort == option {
                                    Label(option.title, systemImage: "checkmark")
                                } else {
                                    Label(option.title, systemImage: option.systemImage)
                                }
                            }
                        }
                    } label: {
                        Image(systemName: "arrow.up.arrow.down.circle")
                    }
                    .accessibilityLabel("Sort shows")

                    Button {
                        currentViewMode = alternateViewMode
                    } label: {
                        Image(systemName: alternateViewMode.systemImage)
                    }
                    .accessibilityLabel(alternateViewMode.accessibilityLabel)
                }

                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Refresh") {
                            Task {
                                await reload(force: true)
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
                await reload(force: false)
            }
            .refreshable {
                await reload(force: true)
            }
            .onChange(of: sourceRecords) { _, newValue in
                records = newValue
            }
            .alert("List Error", isPresented: Binding(
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

    private var listContent: some View {
        List {
            ForEach(displayedRecords) { record in
                recordRow(for: record)
            }
            .onMove(perform: moveRecords)
        }
        .listStyle(.plain)
        .disabled(isSavingCustomOrder)
        .environment(
            \.editMode,
            .constant(isCustomSortEnabled ? EditMode.active : EditMode.inactive)
        )
    }

    private var galleryContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                if isCustomSortEnabled {
                    Label("Switch to list view to reorder shows.", systemImage: "info.circle")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                LazyVGrid(columns: galleryColumns, spacing: 16) {
                    ForEach(displayedRecords) { record in
                        GalleryRecordTile(
                            record: record,
                            currentListType: listType,
                            isBusy: busyRecordID == record.id,
                            onMove: { destination in
                                move(record, to: destination)
                            },
                            onRemove: {
                                remove(record)
                            }
                        )
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .disabled(isSavingCustomOrder)
    }

    @ViewBuilder
    private var emptyState: some View {
        if apiService.isRecordsLoading {
            ProgressView("Loading shows...")
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && records.isEmpty {
            ContentUnavailableView(
                "\(listType.title) is empty",
                systemImage: listType.emptyStateSymbol,
                description: Text("Use the Search or AI tabs to add shows.")
            )
        } else {
            ContentUnavailableView.search(text: query)
        }
    }

    private func reload(force: Bool) async {
        do {
            try await apiService.refreshRecords(force: force)
            records = sourceRecords
        } catch {
            if apiService.isAuthenticated {
                errorMessage = message(for: error)
            }
        }
    }

    private func remove(_ record: Record) {
        guard busyRecordID == nil else { return }

        busyRecordID = record.id
        Task {
            defer { busyRecordID = nil }
            do {
                try await apiService.removeRecord(record)
            } catch {
                errorMessage = message(for: error)
            }
        }
    }

    private func move(_ record: Record, to destination: ListType) {
        guard busyRecordID == nil else { return }

        busyRecordID = record.id
        Task {
            defer { busyRecordID = nil }
            do {
                try await apiService.moveRecord(record, to: destination)
            } catch {
                errorMessage = message(for: error)
            }
        }
    }

    @ViewBuilder
    private func recordRow(for record: Record) -> some View {
        if isCustomSortEnabled {
            baseRecordRow(for: record)
        } else {
            baseRecordRow(for: record)
                .swipeActions {
                    Button(role: .destructive) {
                        remove(record)
                    } label: {
                        Label("Remove", systemImage: "trash")
                    }
                }
        }
    }

    private func baseRecordRow(for record: Record) -> some View {
        RecordRow(
            record: record,
            currentListType: listType,
            isBusy: busyRecordID == record.id,
            onMove: { destination in
                move(record, to: destination)
            },
            onRemove: {
                remove(record)
            },
            onRatingError: { error in
                errorMessage = message(for: error)
            }
        )
        .moveDisabled(!isCustomSortEnabled || isSavingCustomOrder || busyRecordID != nil)
    }

    private func moveRecords(from source: IndexSet, to destination: Int) {
        guard isCustomSortEnabled, busyRecordID == nil, !isSavingCustomOrder else {
            return
        }

        let previousRecords = records
        var reorderedFilteredRecords = displayedRecords
        reorderedFilteredRecords.move(fromOffsets: source, toOffset: destination)

        let reorderedIDs = Set(reorderedFilteredRecords.map(\.id))
        let remainingRecords = previousRecords
            .filter { !reorderedIDs.contains($0.id) }
            .sorted(by: customOrderComparator)

        let updatedRecords = reorderedFilteredRecords.enumerated().map { index, record in
            record.updating(order: index + 1)
        } + remainingRecords.enumerated().map { index, record in
            record.updating(order: reorderedFilteredRecords.count + index + 1)
        }

        records = updatedRecords
        persistCustomOrder(previousRecords: previousRecords, updatedRecords: updatedRecords)
    }

    private func persistCustomOrder(previousRecords: [Record], updatedRecords: [Record]) {
        let orderUpdates = updatedRecords.map { RecordOrderUpdate(id: $0.id, order: $0.order) }
        isSavingCustomOrder = true

        Task { @MainActor in
            defer { isSavingCustomOrder = false }

            do {
                try await apiService.saveRecordOrder(orderUpdates, for: listType)
            } catch {
                records = previousRecords
                errorMessage = message(for: error)
            }
        }
    }

    private func ratingValue(for record: Record) -> Double {
        if listType == .watched {
            return Double(record.rating)
        }
        return record.show.imdbRating ?? 0
    }

    private func customOrderComparator(_ lhs: Record, _ rhs: Record) -> Bool {
        if lhs.order == rhs.order {
            return lhs.additionDate > rhs.additionDate
        }
        return lhs.order < rhs.order
    }

    private func message(for error: Error) -> String {
        if let apiError = error as? APIError {
            return apiError.localizedDescription
        }
        return error.localizedDescription
    }
}

private struct RecordRow: View {
    let record: Record
    let currentListType: ListType
    let isBusy: Bool
    let onMove: (ListType) -> Void
    let onRemove: () -> Void
    let onRatingError: (Error) -> Void

    @EnvironmentObject private var apiService: APIService
    @State private var currentRating: Int
    @State private var isUpdatingRating = false

    private var providerNames: String {
        record.providerRecords.map(\.provider.name).joined(separator: ", ")
    }

    init(
        record: Record,
        currentListType: ListType,
        isBusy: Bool,
        onMove: @escaping (ListType) -> Void,
        onRemove: @escaping () -> Void,
        onRatingError: @escaping (Error) -> Void
    ) {
        self.record = record
        self.currentListType = currentListType
        self.isBusy = isBusy
        self.onMove = onMove
        self.onRemove = onRemove
        self.onRatingError = onRatingError
        self._currentRating = State(initialValue: record.rating)
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            PosterThumbnail(url: record.show.posterURL)

            VStack(alignment: .leading, spacing: 8) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(record.show.title)
                        .font(.headline)
                        .lineLimit(2)

                    if record.show.titleOriginal != record.show.title {
                        Text(record.show.titleOriginal)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                }

                if let overview = record.show.overview, !overview.isEmpty {
                    Text(overview)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(3)
                }

                metadata

                if currentListType == .watched {
                    StarRatingView(
                        currentRating: currentRating,
                        isUpdating: isUpdatingRating || isBusy,
                        onRatingTap: updateRating
                    )
                } else if record.rating > 0 {
                    Label("\(record.rating)/5", systemImage: "star.fill")
                        .font(.caption)
                        .foregroundStyle(.yellow)
                }

                if !record.comment.isEmpty {
                    Text(record.comment)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .lineLimit(3)
                }

                if !providerNames.isEmpty {
                    Text("Watch on: \(providerNames)")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
            }

            Spacer(minLength: 8)

            RecordActionsMenu(
                currentListType: currentListType,
                isBusy: isBusy,
                onMove: onMove,
                onRemove: onRemove
            ) {
                Image(systemName: "ellipsis.circle")
                    .font(.title3)
            }
        }
        .padding(.vertical, 4)
        .onChange(of: record.rating) { _, newValue in
            currentRating = newValue
        }
    }

    @ViewBuilder
    private var metadata: some View {
        HStack(spacing: 10) {
            if let firstAirDate = record.show.firstAirDate {
                Label(firstAirDate, systemImage: "calendar")
            }

            if let imdbRating = record.show.imdbRating {
                Label(String(format: "%.1f", imdbRating), systemImage: "star.leadinghalf.filled")
            }

            if let status = record.show.status, !status.isEmpty {
                Label(status, systemImage: "dot.radiowaves.left.and.right")
            }
        }
        .font(.caption)
        .foregroundStyle(.secondary)
    }

    private func updateRating(to rating: Int) {
        guard !isBusy, !isUpdatingRating else { return }

        isUpdatingRating = true

        Task { @MainActor in
            defer { isUpdatingRating = false }

            do {
                try await apiService.updateRecordRating(recordId: record.id, rating: rating)
                currentRating = rating
            } catch {
                onRatingError(error)
            }
        }
    }
}

private struct StarRatingView: View {
    let currentRating: Int
    let isUpdating: Bool
    let onRatingTap: (Int) -> Void

    var body: some View {
        HStack(spacing: 6) {
            ForEach(1 ... 5, id: \.self) { rating in
                Button {
                    onRatingTap(currentRating == rating ? 0 : rating)
                } label: {
                    Image(systemName: rating <= currentRating ? "star.fill" : "star")
                        .font(.body)
                        .foregroundStyle(rating <= currentRating ? .yellow : .secondary.opacity(0.4))
                }
                .buttonStyle(.plain)
                .disabled(isUpdating)
                .accessibilityLabel(currentRating == rating ? "Clear \(rating)-star rating" : "Set \(rating)-star rating")
            }

            if isUpdating {
                ProgressView()
                    .controlSize(.small)
            } else {
                Text(currentRating > 0 ? "\(currentRating)/5" : "Unrated")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Your rating")
        .accessibilityValue(currentRating > 0 ? "\(currentRating) out of 5" : "Unrated")
    }
}

private struct GalleryRecordTile: View {
    let record: Record
    let currentListType: ListType
    let isBusy: Bool
    let onMove: (ListType) -> Void
    let onRemove: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            PosterArtwork(url: record.show.posterURL)
                .overlay(alignment: .topTrailing) {
                    RecordActionsMenu(
                        currentListType: currentListType,
                        isBusy: isBusy,
                        onMove: onMove,
                        onRemove: onRemove
                    ) {
                        Image(systemName: "ellipsis")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.primary)
                            .padding(8)
                            .background(.ultraThinMaterial, in: Circle())
                    }
                    .padding(8)
                }

            VStack(alignment: .leading, spacing: 4) {
                Text(record.show.title)
                    .font(.subheadline.weight(.semibold))
                    .lineLimit(2)

                if record.rating > 0 {
                    Label("\(record.rating)/5", systemImage: "star.fill")
                        .font(.caption)
                        .foregroundStyle(.yellow)
                }

                if let firstAirDate = record.show.firstAirDate {
                    Text(firstAirDate)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

private struct RecordActionsMenu<MenuLabel: View>: View {
    let currentListType: ListType
    let isBusy: Bool
    let onMove: (ListType) -> Void
    let onRemove: () -> Void

    private let label: MenuLabel

    private var destinationLists: [ListType] {
        ListType.allCases.filter { $0 != currentListType }
    }

    init(
        currentListType: ListType,
        isBusy: Bool,
        onMove: @escaping (ListType) -> Void,
        onRemove: @escaping () -> Void,
        @ViewBuilder label: () -> MenuLabel
    ) {
        self.currentListType = currentListType
        self.isBusy = isBusy
        self.onMove = onMove
        self.onRemove = onRemove
        self.label = label()
    }

    var body: some View {
        Menu {
            ForEach(destinationLists) { destination in
                Button {
                    onMove(destination)
                } label: {
                    Label("Move to \(destination.title)", systemImage: destination.systemImage)
                }
            }

            Divider()

            Button(role: .destructive, action: onRemove) {
                Label("Remove", systemImage: "trash")
            }
        } label: {
            if isBusy {
                ProgressView()
                    .controlSize(.small)
                    .padding(8)
                    .background(.ultraThinMaterial, in: Circle())
            } else {
                label
            }
        }
        .disabled(isBusy)
    }
}

private struct PosterArtwork: View {
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

struct PosterThumbnail: View {
    let url: URL?
    var width: CGFloat = 64
    var height: CGFloat = 96

    var body: some View {
        AsyncImage(url: url) { image in
            image
                .resizable()
                .scaledToFill()
        } placeholder: {
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.gray.opacity(0.2))
                .overlay {
                    Image(systemName: "tv")
                        .foregroundStyle(.secondary)
                }
        }
        .frame(width: width, height: height)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}
