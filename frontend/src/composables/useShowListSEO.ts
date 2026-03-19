import { useHead } from "@vueuse/head";
import { computed, unref } from "vue";

import type { RecordType } from "../types";
import type { ComputedRef, MaybeRef, Ref } from "vue";

export interface ShowListSEOData {
    listType: "watched" | "watching" | "to-watch" | "custom";
    username?: string;
    displayName?: string;
    isPublic?: boolean;
    shows: RecordType[];
    totalCount: number;
    userAvatar?: string;
    listDescription?: string;
}

export function useShowListSEO(
    data:
        | MaybeRef<ShowListSEOData>
        | Ref<ShowListSEOData>
        | ComputedRef<ShowListSEOData>,
): {
    pageTitle: ComputedRef<string>;
    pageDescription: ComputedRef<string>;
    fullUrl: ComputedRef<string>;
    imageUrl: ComputedRef<string>;
} {
    const listData = computed(() => unref(data));

    const baseUrl = computed(() => {
        if (typeof window !== "undefined") {
            return window.location.origin;
        }
        return "https://shows.samarchyan.me";
    });

    const listTypeDisplay = computed(() => {
        const type = listData.value.listType;
        switch (type) {
            case "watched":
                return "Watched Shows";
            case "watching":
                return "Currently Watching";
            case "to-watch":
                return "Watchlist";
            case "custom":
                return "Show Collection";
            default:
                return "Show List";
        }
    });

    const fullUrl = computed(() => {
        const d = listData.value;
        if (d.username) {
            let listPath: string;
            if (d.listType === "watched") {
                listPath = "watched";
            } else if (d.listType === "watching") {
                listPath = "watching";
            } else {
                listPath = "to-watch";
            }
            return `${baseUrl.value}/users/${d.username}/list/${listPath}`;
        }
        return `${baseUrl.value}/list`;
    });

    const pageTitle = computed(() => {
        const d = listData.value;
        const userDisplay =
            d.displayName || (d.username ? `@${d.username}` : "");

        if (d.username && userDisplay) {
            return `${userDisplay}'s ${listTypeDisplay.value} (${d.totalCount} shows) | Shows`;
        }

        return `My ${listTypeDisplay.value} (${d.totalCount} shows) | Shows`;
    });

    const pageDescription = computed(() => {
        const d = listData.value;
        const userDisplay =
            d.displayName || (d.username ? `@${d.username}` : "");

        // Get top show titles for description
        const topShows = d.shows
            .slice(0, 5)
            .map((show) => show.show.title)
            .filter(Boolean);

        const showsText =
            topShows.length > 0
                ? `Including ${topShows.slice(0, 3).join(", ")}${topShows.length > 3 ? " and more" : ""}.`
                : "";

        const baseDesc =
            d.listDescription ||
            `Discover ${d.totalCount} shows in ${userDisplay ? `${userDisplay}'s` : "this"} ${listTypeDisplay.value.toLowerCase()}. ${showsText}`;

        const actionText =
            d.listType === "watched"
                ? "See what they've watched and get personalized show recommendations."
                : "Explore their watchlist and find your next great show to watch.";

        return `${baseDesc} ${d.isPublic && d.username ? actionText : "Track shows, discover more on Shows."}`;
    });

    const keywordsComputed = computed(() => {
        const d = listData.value;
        const baseKeywords = [
            "show list",
            "tv collection",
            d.listType === "watched" ? "watched shows" : "watchlist",
            d.listType === "watched" ? "show diary" : "shows to watch",
            "show recommendations",
            "tv tracker",
        ];

        // Add show titles as keywords
        const showKeywords = d.shows
            .slice(0, 10)
            .map((show) => show.show.title?.toLowerCase())
            .filter(Boolean);

        // Add user-specific keywords
        const userKeywords = d.username
            ? [`${d.username} shows`, `${d.username} ${d.listType}`]
            : [];

        // Add genre keywords from shows
        const genreKeywords = [
            ...new Set(
                d.shows
                    .map((show) => show.show.genre)
                    .filter((genre): genre is string => Boolean(genre))
                    .flatMap((genre) => genre.split(", "))
                    .slice(0, 5),
            ),
        ];

        return [
            ...baseKeywords,
            ...showKeywords.filter((keyword): keyword is string =>
                Boolean(keyword),
            ),
            ...userKeywords,
            ...genreKeywords,
        ].join(", ");
    });

    const imageUrl = computed(() => {
        const d = listData.value;

        // Use user avatar if available
        if (d.userAvatar && typeof d.userAvatar === "string") {
            return d.userAvatar.startsWith("http")
                ? d.userAvatar
                : `${baseUrl.value}${d.userAvatar}`;
        }

        // Use first show poster if available
        const firstShowWithPoster = d.shows.find((show) => show.show.hasPoster);
        if (firstShowWithPoster?.show.posterNormal) {
            return firstShowWithPoster.show.posterNormal;
        }

        // Fallback to Shows logo
        return `${baseUrl.value}/img/logo.png`;
    });

    useHead({
        title: pageTitle,
        meta: [
            { name: "description", content: pageDescription },
            { name: "keywords", content: keywordsComputed },
            {
                name: "author",
                content:
                    listData.value.displayName ||
                    listData.value.username ||
                    "Shows",
            },

            // Open Graph
            { property: "og:type", content: "website" },
            { property: "og:title", content: pageTitle },
            { property: "og:description", content: pageDescription },
            { property: "og:image", content: imageUrl },
            { property: "og:url", content: fullUrl },
            { property: "og:site_name", content: "Shows" },

            // Twitter Card
            { name: "twitter:card", content: "summary_large_image" },
            { name: "twitter:title", content: pageTitle },
            { name: "twitter:description", content: pageDescription },
            { name: "twitter:image", content: imageUrl },
            { name: "twitter:site", content: "@Shows" },

            // List-specific meta tags
            {
                name: "robots",
                content: listData.value.isPublic
                    ? "index, follow"
                    : "noindex, nofollow",
            },
            { property: "article:section", content: "Shows" },
            { property: "article:tag", content: listTypeDisplay },
            { name: "theme-color", content: "#667eea" },
        ],
        link: [{ rel: "canonical", href: fullUrl }],
    });

    return {
        pageTitle,
        pageDescription,
        fullUrl,
        imageUrl,
    };
}
