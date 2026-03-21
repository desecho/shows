import { useHead } from "@vueuse/head";
import { computed, unref } from "vue";

import type { ComputedRef, MaybeRef } from "vue";

export interface ShowStructuredData {
    title: string;
    year?: number;
    rating?: number;
    genre?: string[];
    cast?: string[];
    plot?: string;
    poster?: string;
    datePublished?: string;
    contentRating?: string;
}

export interface PersonStructuredData {
    name: string;
    jobTitle?: string;
    image?: string;
    description?: string;
    sameAs?: string[];
}

export interface OrganizationStructuredData {
    name: string;
    description: string;
    url: string;
    logo: string;
    sameAs: string[];
}

export function useShowStructuredData(show: MaybeRef<ShowStructuredData>): {
    structuredData: ComputedRef<Record<string, unknown>>;
} {
    const showData = computed(() => unref(show));

    const structuredData = computed(() => {
        const s = showData.value;

        const schema: Record<string, unknown> = {
            "@context": "https://schema.org",
            "@type": "TVSeries",
            name: s.title,
            ...(s.plot && { description: s.plot }),
            ...(s.year && { dateCreated: s.year.toString() }),
            ...(s.datePublished && { datePublished: s.datePublished }),
            ...(s.contentRating && { contentRating: s.contentRating }),
            ...(s.poster && {
                image: {
                    "@type": "ImageObject",
                    url: s.poster,
                },
            }),
            ...(s.genre && s.genre.length > 0 && { genre: s.genre }),
            ...(s.cast &&
                s.cast.length > 0 && {
                    actor: s.cast.map((actor) => ({
                        "@type": "Person",
                        name: actor,
                    })),
                }),
            ...(s.rating && {
                aggregateRating: {
                    "@type": "AggregateRating",
                    ratingValue: s.rating,
                    ratingCount: 1,
                    bestRating: 10,
                    worstRating: 1,
                },
            }),
        };

        return schema;
    });

    useHead({
        script: [
            {
                type: "application/ld+json",
                children: JSON.stringify(structuredData.value),
            },
        ],
    });

    return { structuredData };
}

export function usePersonStructuredData(
    person: MaybeRef<PersonStructuredData>,
): {
    structuredData: ComputedRef<Record<string, unknown>>;
} {
    const personData = computed(() => unref(person));

    const structuredData = computed(() => {
        const p = personData.value;

        return {
            "@context": "https://schema.org",
            "@type": "Person",
            name: p.name,
            ...(p.jobTitle && { jobTitle: p.jobTitle }),
            ...(p.image && {
                image: {
                    "@type": "ImageObject",
                    url: p.image,
                },
            }),
            ...(p.description && { description: p.description }),
            ...(p.sameAs && p.sameAs.length > 0 && { sameAs: p.sameAs }),
        };
    });

    useHead({
        script: [
            {
                type: "application/ld+json",
                children: JSON.stringify(structuredData.value),
            },
        ],
    });

    return { structuredData };
}

export function useOrganizationStructuredData(
    org: MaybeRef<OrganizationStructuredData>,
): {
    structuredData: ComputedRef<Record<string, unknown>>;
} {
    const orgData = computed(() => unref(org));

    const structuredData = computed(() => {
        const o = orgData.value;

        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            name: o.name,
            description: o.description,
            url: o.url,
            logo: {
                "@type": "ImageObject",
                url: o.logo,
            },
            sameAs: o.sameAs,
        };
    });

    useHead({
        script: [
            {
                type: "application/ld+json",
                children: JSON.stringify(structuredData.value),
            },
        ],
    });

    return { structuredData };
}

export function useBreadcrumbStructuredData(
    breadcrumbs: MaybeRef<Array<{ name: string; url: string }>>,
): {
    structuredData: ComputedRef<Record<string, unknown>>;
} {
    const breadcrumbData = computed(() => unref(breadcrumbs));

    const structuredData = computed(() => ({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: breadcrumbData.value.map((item, index) => ({
            "@type": "ListItem",
            position: index + 1,
            name: item.name,
            item: item.url.startsWith("http")
                ? item.url
                : `${window?.location?.origin || ""}${item.url}`,
        })),
    }));

    useHead({
        script: [
            {
                type: "application/ld+json",
                children: JSON.stringify(structuredData.value),
            },
        ],
    });

    return { structuredData };
}

export interface ShowListItem {
    title: string;
    year?: number;
    genre?: string[];
    poster?: string;
    rating?: number;
    url?: string;
}

export interface ShowListStructuredData {
    name: string;
    description: string;
    numberOfItems: number;
    shows: ShowListItem[];
    author?: {
        name: string;
        url?: string;
        image?: string;
    };
    url?: string;
    dateCreated?: string;
    dateModified?: string;
}

export function useShowListStructuredData(
    listData: MaybeRef<ShowListStructuredData>,
): {
    structuredData: ComputedRef<Record<string, unknown>>;
} {
    const showListData = computed(() => unref(listData));

    const structuredData = computed(() => {
        const data = showListData.value;

        const schema: Record<string, unknown> = {
            "@context": "https://schema.org",
            "@type": ["ItemList", "CreativeWork"],
            name: data.name,
            description: data.description,
            numberOfItems: data.numberOfItems,
            ...(data.url && { url: data.url }),
            ...(data.dateCreated && { dateCreated: data.dateCreated }),
            ...(data.dateModified && { dateModified: data.dateModified }),
            ...(data.author && {
                author: {
                    "@type": "Person",
                    name: data.author.name,
                    ...(data.author.url && { url: data.author.url }),
                    ...(data.author.image && {
                        image: {
                            "@type": "ImageObject",
                            url: data.author.image,
                        },
                    }),
                },
            }),
            itemListElement: data.shows.map((show, index) => ({
                "@type": "ListItem",
                position: index + 1,
                item: {
                    "@type": "TVSeries",
                    name: show.title,
                    ...(show.year && { dateCreated: show.year.toString() }),
                    ...(show.genre &&
                        show.genre.length > 0 && { genre: show.genre }),
                    ...(show.poster && {
                        image: {
                            "@type": "ImageObject",
                            url: show.poster,
                        },
                    }),
                    ...(show.rating && {
                        aggregateRating: {
                            "@type": "AggregateRating",
                            ratingValue: show.rating,
                            ratingCount: 1,
                            bestRating: 10,
                            worstRating: 1,
                        },
                    }),
                    ...(show.url && { url: show.url }),
                },
            })),
        };

        return schema;
    });

    useHead({
        script: [
            {
                type: "application/ld+json",
                children: JSON.stringify(structuredData.value),
            },
        ],
    });

    return { structuredData };
}
