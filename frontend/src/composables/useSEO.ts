import { useHead } from "@vueuse/head";
import { computed, unref } from "vue";

import type { ComputedRef, MaybeRef } from "vue";

export interface SEOData {
    title?: string;
    description?: string;
    keywords?: string[];
    image?: string;
    url?: string;
    type?: "website" | "article" | "profile";
    author?: string;
    publishedTime?: string;
    modifiedTime?: string;
}

export interface ShowSEO {
    title: string;
    year?: number;
    rating?: number;
    genre?: string[];
    cast?: string[];
    plot?: string;
    poster?: string;
    runtime?: number;
}

export interface UserProfileSEO {
    username: string;
    displayName?: string;
    bio?: string;
    avatar?: string;
    showsWatched?: number;
    followersCount?: number;
}

export function useSEO(data: MaybeRef<SEOData>): {
    pageTitle: ComputedRef<string>;
    pageDescription: ComputedRef<string>;
    fullUrl: ComputedRef<string>;
    imageUrl: ComputedRef<string>;
} {
    const seoData = computed(() => unref(data));

    const baseUrl = computed(() => {
        if (typeof window !== "undefined") {
            return window.location.origin;
        }
        return "https://shows.samarchyan.me"; // Fallback for SSR
    });

    const fullUrl = computed(() => {
        const url = seoData.value.url || "";
        return url.startsWith("http") ? url : `${baseUrl.value}${url}`;
    });

    const pageTitle = computed(() => {
        const title = seoData.value.title;
        return title
            ? `${title} | Shows`
            : "Shows - Track Shows, Discover More";
    });

    const pageDescription = computed(
        () =>
            seoData.value.description ||
            "Track what you watch. Discover what to watch next. Join the Shows community for personalized show recommendations.",
    );

    const keywordsString = computed(() => {
        const baseKeywords = [
            "shows",
            "tv",
            "series",
            "watch",
            "tracking",
            "recommendations",
        ];
        const customKeywords = seoData.value.keywords || [];
        return [...baseKeywords, ...customKeywords].join(", ");
    });

    const imageUrl = computed(() => {
        const image = seoData.value.image;
        if (!image) {
            return `${baseUrl.value}/img/logo.png`;
        }
        return image.startsWith("http") ? image : `${baseUrl.value}${image}`;
    });

    useHead({
        title: pageTitle,
        meta: [
            { name: "description", content: pageDescription },
            { name: "keywords", content: keywordsString },
            { name: "author", content: seoData.value.author || "Shows" },

            // Open Graph
            { property: "og:type", content: seoData.value.type || "website" },
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

            // Additional meta tags
            { name: "robots", content: "index, follow" },
            {
                name: "viewport",
                content: "width=device-width, initial-scale=1",
            },
            {
                "http-equiv": "Content-Type",
                content: "text/html; charset=UTF-8",
            },
        ],
        link: [
            { rel: "canonical", href: fullUrl },
            { rel: "icon", type: "image/png", href: "/favicon.png" },
        ],
        // Add structured data if provided
        ...(seoData.value.publishedTime && {
            meta: [
                {
                    property: "article:published_time",
                    content: seoData.value.publishedTime,
                },
                ...(seoData.value.modifiedTime
                    ? [
                          {
                              property: "article:modified_time",
                              content: seoData.value.modifiedTime,
                          },
                      ]
                    : []),
            ],
        }),
    });

    return {
        pageTitle,
        pageDescription,
        fullUrl,
        imageUrl,
    };
}

export function useShowSEO(show: MaybeRef<ShowSEO>): {
    pageTitle: ComputedRef<string>;
    pageDescription: ComputedRef<string>;
    fullUrl: ComputedRef<string>;
    imageUrl: ComputedRef<string>;
} {
    const showData = computed(() => unref(show));

    const seoData = computed<SEOData>(() => {
        const s = showData.value;
        const yearText = s.year ? ` (${s.year})` : "";
        const ratingText = s.rating ? ` - ${s.rating}/10` : "";

        return {
            title: `${s.title}${yearText}`,
            description:
                s.plot ||
                `Watch ${s.title}${yearText} on Shows. ${s.genre?.length ? `Genres: ${s.genre.join(", ")}. ` : ""}${ratingText}`,
            keywords: [
                s.title.toLowerCase(),
                ...(s.genre || []),
                ...(s.cast?.slice(0, 3) || []),
                ...(s.year ? [s.year.toString()] : []),
            ],
            image: s.poster,
            type: "article",
        };
    });

    return useSEO(seoData);
}

export function useUserProfileSEO(user: MaybeRef<UserProfileSEO>): {
    pageTitle: ComputedRef<string>;
    pageDescription: ComputedRef<string>;
    fullUrl: ComputedRef<string>;
    imageUrl: ComputedRef<string>;
} {
    const userData = computed(() => unref(user));

    const seoData = computed<SEOData>(() => {
        const u = userData.value;
        const statsText = u.showsWatched
            ? ` - ${u.showsWatched} shows watched`
            : "";
        const followersText = u.followersCount
            ? `, ${u.followersCount} followers`
            : "";

        return {
            title: u.displayName || `@${u.username}`,
            description:
                u.bio ||
                `${u.displayName || `@${u.username}`}'s show profile on Shows${statsText}${followersText}. Discover their show taste and get personalized recommendations.`,
            keywords: [
                u.username,
                ...(u.displayName ? [u.displayName] : []),
                "show profile",
                "tv enthusiast",
                "show recommendations",
            ],
            image: u.avatar,
            type: "profile",
            url: `/users/${u.username}`,
        };
    });

    return useSEO(seoData);
}
