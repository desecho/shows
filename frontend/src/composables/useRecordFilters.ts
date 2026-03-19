import { debounce } from "lodash";
import { computed, type ComputedRef, ref, type Ref } from "vue";

import type { RecordType } from "../types";

import { listToWatchId, listWatchedId } from "../const";

export function useRecordFilters(
    records: Ref<RecordType[]>,
    currentListId: Ref<number>,
    initialQuery = "",
): {
    query: Ref<string>;
    debouncedQuery: Ref<string>;
    setQuery: (value: string) => void;
    getFilteredRecords: (filters: {
        hideUnreleasedShows: Ref<boolean>;
        recentReleasesFilter: Ref<boolean>;
    }) => ComputedRef<RecordType[]>;
    filterRecords: (
        recordsArray: RecordType[],
        searchQuery: string,
        listId: number,
        filters: {
            hideUnreleased: boolean;
            recentReleases: boolean;
        },
    ) => RecordType[];
    getWatchedCount: () => ComputedRef<number>;
    getToWatchCount: () => ComputedRef<number>;
} {
    const query = ref(initialQuery);
    const debouncedQuery = ref(initialQuery);

    // Debounced search - updates after 300ms of no typing
    const updateDebouncedQuery = debounce((value: string) => {
        debouncedQuery.value = value;
    }, 300);

    // Watch for query changes and debounce them
    function setQuery(value: string): void {
        query.value = value;
        updateDebouncedQuery(value);
    }

    // Memoized search filter
    function searchMatchesRecord(
        record: RecordType,
        searchQuery: string,
    ): boolean {
        if (!searchQuery) {
            return true;
        }

        const q = searchQuery.toLowerCase();
        return (
            record.show.title.toLowerCase().includes(q) ||
            record.show.titleOriginal.toLowerCase().includes(q) ||
            (record.show.actors !== "" &&
                record.show.actors.toLowerCase().includes(q))
        );
    }

    // Memoized unreleased filter
    function releasedMatchesRecord(
        record: RecordType,
        filterEnabled: boolean,
        listId: number,
    ): boolean {
        if (!filterEnabled || listId !== listToWatchId) {
            return true;
        }

        return record.show.isReleased;
    }

    // Memoized recent releases filter
    function recentReleasesMatchesRecord(
        record: RecordType,
        filterEnabled: boolean,
        listId: number,
    ): boolean {
        if (!filterEnabled || listId !== listToWatchId) {
            return true;
        }

        if (!record.show.firstAirDate || !record.show.firstAirDateTimestamp) {
            return false;
        }

        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        const showFirstAirDate = new Date(
            record.show.firstAirDateTimestamp * 1000,
        );

        return showFirstAirDate >= sixMonthsAgo;
    }

    // Main filtered records function - returns raw filtered array for caching
    function getFilteredRecords(filters: {
        hideUnreleasedShows: Ref<boolean>;
        recentReleasesFilter: Ref<boolean>;
    }): ComputedRef<RecordType[]> {
        return computed(() => {
            const searchQuery = debouncedQuery.value.trim();
            const listId = currentListId.value;

            const result = records.value.filter((record) => {
                // List filter - must match current list
                if (record.listId !== listId) {
                    return false;
                }

                // Apply all filters using memoized functions with null safety
                let hideUnreleasedValue = false;
                if (typeof filters.hideUnreleasedShows?.value === "boolean") {
                    hideUnreleasedValue = filters.hideUnreleasedShows.value;
                } else if (typeof filters.hideUnreleasedShows === "boolean") {
                    hideUnreleasedValue = filters.hideUnreleasedShows;
                }

                let recentReleasesValue = false;
                if (typeof filters.recentReleasesFilter?.value === "boolean") {
                    recentReleasesValue = filters.recentReleasesFilter.value;
                } else if (typeof filters.recentReleasesFilter === "boolean") {
                    recentReleasesValue = filters.recentReleasesFilter;
                }

                return (
                    searchMatchesRecord(record, searchQuery) &&
                    releasedMatchesRecord(
                        record,
                        hideUnreleasedValue,
                        listId,
                    ) &&
                    recentReleasesMatchesRecord(
                        record,
                        recentReleasesValue,
                        listId,
                    )
                );
            });

            return result;
        });
    }

    // Direct filter function for external caching (non-reactive)
    function filterRecords(
        recordsArray: RecordType[],
        searchQuery: string,
        listId: number,
        filters: {
            hideUnreleased: boolean;
            recentReleases: boolean;
        },
    ): RecordType[] {
        return recordsArray.filter((record) => {
            // List filter - must match current list
            if (record.listId !== listId) {
                return false;
            }

            return (
                searchMatchesRecord(record, searchQuery.trim()) &&
                releasedMatchesRecord(record, filters.hideUnreleased, listId) &&
                recentReleasesMatchesRecord(
                    record,
                    filters.recentReleases,
                    listId,
                )
            );
        });
    }

    // Memoized count computations
    function getWatchedCount(): ComputedRef<number> {
        return computed(() => {
            return records.value.filter(
                (record) => record.listId === listWatchedId,
            ).length;
        });
    }

    function getToWatchCount(): ComputedRef<number> {
        return computed(() => {
            return records.value.filter(
                (record) => record.listId === listToWatchId,
            ).length;
        });
    }

    return {
        query,
        debouncedQuery,
        setQuery,
        getFilteredRecords,
        filterRecords,
        getWatchedCount,
        getToWatchCount,
    };
}
