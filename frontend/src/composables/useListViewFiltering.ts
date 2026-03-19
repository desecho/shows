/**
 * @fileoverview Composable for ListView filtering logic
 *
 * Provides filtering functionality for ListView records including:
 * - List-based filtering (watched vs watching vs to-watch)
 * - Text search across title, actors
 * - Specialized filters (unreleased, recent releases)
 * - Comprehensive error handling and validation
 */

import { computed, type ComputedRef, type Ref } from "vue";

import type { RecordType } from "../types";
import type { ListViewFilters } from "../types/listView";

import {
    isRecentRelease,
    isShowReleased,
    isValidRecord,
    matchesSearchQuery,
} from "../utils/showUtils";

/**
 * Composable for filtering ListView records
 * @param records - Reactive array of all records
 * @param currentListId - Current list ID (1 = watched, 2 = watching, 3 = to-watch)
 * @param searchQuery - Search query string
 * @param filters - Active filter settings
 * @returns Computed array of filtered records
 */
export function useListViewFiltering(
    records: Ref<RecordType[]>,
    currentListId: Ref<number>,
    searchQuery: Ref<string>,
    filters: Ref<ListViewFilters>,
): {
    filteredRecords: ComputedRef<RecordType[]>;
    matchesUnreleasedFilter: (
        record: RecordType,
        filterEnabled: boolean,
        listId: number,
    ) => boolean;
    matchesRecentReleasesFilter: (
        record: RecordType,
        filterEnabled: boolean,
        listId: number,
    ) => boolean;
} {
    // Helper functions using shared utilities
    function matchesUnreleasedFilter(
        record: RecordType,
        filterEnabled: boolean,
        listId: number,
    ): boolean {
        return !filterEnabled || listId !== 3 || isShowReleased(record);
    }

    function matchesRecentReleasesFilter(
        record: RecordType,
        filterEnabled: boolean,
        listId: number,
    ): boolean {
        return (
            !filterEnabled ||
            listId !== 3 ||
            isRecentRelease(record.show?.firstAirDateTimestamp, 6)
        );
    }

    /**
     * Main filtered records computation
     */
    const filteredRecords = computed(() => {
        try {
            if (
                !records.value ||
                !Array.isArray(records.value) ||
                records.value.length === 0
            ) {
                return [];
            }

            const query = searchQuery.value?.trim() || "";
            const listId = currentListId.value;
            const currentFilters = filters.value;

            return records.value.filter((record) => {
                try {
                    // Validate record structure
                    if (!isValidRecord(record)) {
                        console.warn("Invalid record structure:", record);
                        return false;
                    }

                    // Basic list filter - must match current list
                    if (record.listId !== listId) {
                        return false;
                    }

                    // Apply all filters
                    return (
                        matchesSearchQuery(record, query) &&
                        matchesUnreleasedFilter(
                            record,
                            currentFilters?.hideUnreleased ?? false,
                            listId,
                        ) &&
                        matchesRecentReleasesFilter(
                            record,
                            currentFilters?.recentReleases ?? false,
                            listId,
                        )
                    );
                } catch (recordError) {
                    console.warn(
                        "Error processing record:",
                        record?.id || "unknown",
                        recordError,
                    );
                    return false;
                }
            });
        } catch (error) {
            console.error("Error in filteredRecords computation:", error);
            return [];
        }
    });

    return {
        filteredRecords,
        // Export individual filter functions for testing
        matchesUnreleasedFilter,
        matchesRecentReleasesFilter,
    };
}
