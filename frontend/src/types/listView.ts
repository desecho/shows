/**
 * ListView-specific types for mode, sorting, and filtering.
 *
 * @fileoverview Type definitions for ListView components and state management
 */

/**
 * Available view modes for displaying show records
 */
export type ViewMode =
    /** Full detailed view with all show information */
    | "full"
    /** Compact view with essential information only */
    | "minimal"
    /** Grid-based visual layout showing posters */
    | "gallery"
    /** Reduced size full view */
    | "compact";

/**
 * Available sorting methods for show records
 */
export type SortType =
    /** Sort by when the show was added to the list */
    | "additionDate"
    /** Sort by show first air date */
    | "releaseDate"
    /** Sort by user rating (watched) or IMDB rating (to-watch) */
    | "rating"
    /** Custom drag-and-drop ordering */
    | "custom";

/**
 * Filter options for refining the displayed show list
 */
export interface ListViewFilters {
    /** Hide shows that haven't been released yet (to-watch list only) */
    hideUnreleased: boolean;
    /** Show only shows released in the last 6 months (to-watch list only) */
    recentReleases: boolean;
}

/**
 * Complete state representation for ListView functionality
 */
export interface ListViewState {
    /** Current view mode */
    mode: ViewMode;
    /** Current sorting method */
    sort: SortType;
    /** Search query string */
    query: string;
    /** Active filter settings */
    filters: ListViewFilters;
    /** Current page number (1-based) */
    page: number;
}

/**
 * Props for components that need list context information
 */
export interface ListContextProps {
    /** ID of the current list (1 = watched, 2 = watching, 3 = to-watch) */
    currentListId: number;
    /** Whether viewing another user's profile */
    isProfileView: boolean;
}

/**
 * Props for components that handle view mode selection
 */
export interface ViewModeProps {
    /** Current view mode */
    mode: ViewMode;
}

/**
 * Props for components that handle sorting functionality
 */
export interface SortProps {
    /** Current sort type */
    sort: SortType;
}
