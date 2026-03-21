export interface JWTDecoded {
    token_type: string;
    exp: number;
    iat: number;
    jti: string;
    user_id: number;
}

export interface ShowPreview {
    id: number;
    tmdbLink: string;
    firstAirDate: string;
    title: string;
    titleOriginal: string;
    poster: string;
    poster2x: string;
    isReleased: boolean;
    hidden: boolean;
}

export interface AddToListFromDbResponseData {
    status: string;
}

export interface Trailer {
    url: string;
    name: string;
}

export interface Show {
    id: number;
    title: string;
    titleOriginal: string;
    isReleased: boolean;
    posterNormal: string;
    posterBig: string;
    posterSmall: string;
    imdbRating: number;
    imdbRatingConverted: number;
    firstAirDate: string;
    firstAirDateTimestamp: number;
    country: string;
    writer: string;
    genre: string;
    actors: string;
    overview: string;
    status: string;
    homepage: string;
    imdbUrl: string;
    tmdbUrl: string;
    trailers: Trailer[];
    hasPoster: boolean;
}

export interface Provider {
    logo: string;
    name: string;
}

export interface ProviderRecord {
    tmdbWatchUrl: string;
    provider: Provider;
}

export interface RecordType {
    id: number;
    order: number;
    comment: string;
    commentArea: boolean;
    rating: number;
    providerRecords: ProviderRecord[];
    show: Show;
    listId: number;
    additionDate: number;
    ratingOriginal: number;
}

export interface SortData {
    id: number;
    order: number;
}

export interface AuthProps {
    userId: number;
    timestamp: number;
    signature: string;
}

export interface ShareResponse {
    share_url: string;
}

export interface ShareRequest {
    platform?: string;
}

export type ListKey = number;
