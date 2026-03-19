"""Types for views."""

from __future__ import annotations

from typing import Optional

from typing_extensions import NotRequired, TypedDict

from ..types import Trailer


class ShowObject(TypedDict):
    """Show object."""

    id: int
    title: str
    titleOriginal: str
    posterSmall: Optional[str]
    posterNormal: Optional[str]
    posterBig: Optional[str]
    isReleased: bool
    imdbRating: Optional[float]
    firstAirDate: Optional[str]
    firstAirDateTimestamp: float
    country: Optional[str]
    writer: Optional[str]
    genre: Optional[str]
    actors: Optional[str]
    overview: Optional[str]
    homepage: Optional[str]
    runtime: Optional[str]
    imdbUrl: str
    tmdbUrl: str
    trailers: list[Trailer]
    hasPoster: bool


class ProviderObject(TypedDict):
    """Provider object."""

    logo: str
    name: str


class ProviderRecordObject(TypedDict):
    """Provider record object."""

    tmdbWatchUrl: str
    provider: ProviderObject


class RecordObject(TypedDict):
    """Record object."""

    id: int
    order: int
    show: ShowObject
    comment: str
    commentArea: bool
    rating: int
    providerRecords: list[ProviderRecordObject]
    listId: NotRequired[Optional[int]]
    additionDate: float


class SearchOptions(TypedDict):
    """Search options."""

    popularOnly: bool
    sortByDate: bool


class ShowListResult(TypedDict):
    """Show search result."""

    id: int
    tmdbLink: str
    firstAirDate: Optional[str]
    title: str
    titleOriginal: str
    poster: Optional[str]
    poster2x: Optional[str]
    isReleased: bool
