/**
 * @fileoverview Shared utility functions for show operations
 *
 * Provides reusable functions for:
 * - Show data validation
 * - Date handling and validation
 * - Text search utilities
 * - Rating calculations
 * - Type guards and validation
 */

import type { RecordType } from "../types";

/**
 * Type guard to validate RecordType structure
 */
export function isValidRecord(record: unknown): record is RecordType {
    return Boolean(
        record &&
        typeof record === "object" &&
        record !== null &&
        "show" in record &&
        "listId" in record &&
        "id" in record &&
        typeof (record as RecordType).listId === "number" &&
        typeof (record as RecordType).show?.title === "string" &&
        (record as RecordType).id !== undefined,
    );
}

/**
 * Type guard to validate show structure within a record
 */
export function hasValidShow(record: RecordType): boolean {
    return (
        record.show &&
        typeof record.show.title === "string" &&
        typeof record.show.titleOriginal === "string"
    );
}

/**
 * Safe number extraction with fallback
 */
export function safeNumber(value: unknown, fallback = 0): number {
    return typeof value === "number" && !isNaN(value) ? value : fallback;
}

/**
 * Safe string extraction with fallback
 */
export function safeString(value: unknown, fallback = ""): string {
    return typeof value === "string" ? value : fallback;
}

/**
 * Safe boolean extraction with fallback
 */
export function safeBoolean(value: unknown, fallback = false): boolean {
    return typeof value === "boolean" ? value : fallback;
}

/**
 * Create a normalized search string from show data
 */
export function createSearchString(record: RecordType): string {
    if (!hasValidShow(record)) {
        return "";
    }

    const parts = [
        safeString(record.show.title),
        safeString(record.show.titleOriginal),
        safeString(record.show.actors),
        safeString(record.show.writer),
    ];

    return parts.filter(Boolean).join(" ").toLowerCase();
}

/**
 * Check if a search query matches a record
 */
export function matchesSearchQuery(record: RecordType, query: string): boolean {
    if (!query.trim()) {
        return true;
    }
    if (!hasValidShow(record)) {
        return false;
    }

    const searchString = createSearchString(record);
    const normalizedQuery = query.toLowerCase().trim();

    return searchString.includes(normalizedQuery);
}

/**
 * Validate and create Date object from timestamp
 */
export function createDateFromTimestamp(timestamp: unknown): Date | null {
    const ts = safeNumber(timestamp, 0);
    if (ts <= 0) {
        return null;
    }

    try {
        const date = new Date(ts * 1000);
        return isNaN(date.getTime()) ? null : date;
    } catch {
        return null;
    }
}

/**
 * Check if a date is within the last N months
 */
export function isRecentRelease(timestamp: unknown, monthsBack = 6): boolean {
    const releaseDate = createDateFromTimestamp(timestamp);
    if (!releaseDate) {
        return false;
    }

    const cutoffDate = new Date();
    cutoffDate.setMonth(cutoffDate.getMonth() - monthsBack);

    return releaseDate >= cutoffDate;
}

/**
 * Get user rating or fallback to 0
 */
export function getUserRating(record: RecordType): number {
    return safeNumber(record.rating, 0);
}

/**
 * Get IMDB rating or fallback to 0
 */
export function getImdbRating(record: RecordType): number {
    return safeNumber(record.show?.imdbRating, 0);
}

/**
 * Get custom order or fallback to 0
 */
export function getCustomOrder(record: RecordType): number {
    return safeNumber(record.order, 0);
}

/**
 * Get addition date timestamp or fallback to 0
 */
export function getAdditionDate(record: RecordType): number {
    return safeNumber(record.additionDate, 0);
}

/**
 * Get first air date timestamp or fallback to 0
 */
export function getFirstAirDate(record: RecordType): number {
    return safeNumber(record.show?.firstAirDateTimestamp, 0);
}

/**
 * Check if show is released
 */
export function isShowReleased(record: RecordType): boolean {
    return safeBoolean(record.show?.isReleased, false);
}

/**
 * Sorting comparison functions
 */
export const sortCompareFunctions = {
    /**
     * Compare by addition date (descending)
     */
    byAdditionDate(a: RecordType, b: RecordType): number {
        return getAdditionDate(b) - getAdditionDate(a);
    },

    /**
     * Compare by first air date (descending)
     */
    byFirstAirDate(a: RecordType, b: RecordType): number {
        return getFirstAirDate(b) - getFirstAirDate(a);
    },

    /**
     * Compare by user rating (descending)
     */
    byUserRating(a: RecordType, b: RecordType): number {
        return getUserRating(b) - getUserRating(a);
    },

    /**
     * Compare by IMDB rating (descending)
     */
    byImdbRating(a: RecordType, b: RecordType): number {
        return getImdbRating(b) - getImdbRating(a);
    },

    /**
     * Compare by custom order (ascending)
     */
    byCustomOrder(a: RecordType, b: RecordType): number {
        return getCustomOrder(a) - getCustomOrder(b);
    },
};

/**
 * Filter predicate functions
 */
export const filterPredicates = {
    /**
     * Filter by list ID
     */
    byListId:
        (listId: number) =>
        (record: RecordType): boolean => {
            return record.listId === listId;
        },

    /**
     * Filter by search query
     */
    bySearchQuery:
        (query: string) =>
        (record: RecordType): boolean => {
            return matchesSearchQuery(record, query);
        },

    /**
     * Filter out unreleased shows (to-watch list only)
     */
    hideUnreleased:
        (listId: number) =>
        (record: RecordType): boolean => {
            return listId !== 3 || isShowReleased(record);
        },

    /**
     * Filter for recent releases (to-watch list only)
     */
    recentReleases:
        (listId: number, monthsBack = 6) =>
        (record: RecordType): boolean => {
            return (
                listId !== 3 ||
                isRecentRelease(record.show?.firstAirDateTimestamp, monthsBack)
            );
        },
};
