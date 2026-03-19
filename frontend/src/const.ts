export const ADMIN_EMAIL = import.meta.env.VITE_ADMIN_EMAIL as string;

// Hardcode list IDs
export const listWatchedId = 1;
export const listWatchingId = 2;
export const listToWatchId = 3;

export const starSizeNormal = 35;
export const starSizeMinimal = 15;

// AI Recommendations constants
export const AI_MAX_RECOMMENDATIONS = 50;
export const AI_MIN_RECOMMENDATIONS = 1;
export const AI_MIN_RATING = 0;
export const AI_MAX_RATING = 5;

// TV Show genres for AI recommendations
export const SHOW_GENRES = [
    "Action & Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Kids",
    "Mystery",
    "News",
    "Reality",
    "Sci-Fi & Fantasy",
    "Soap",
    "Talk",
    "War & Politics",
    "Western",
] as const;
