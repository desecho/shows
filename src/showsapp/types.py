"""Custom Types."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional, TypeAlias

from django.urls import URLPattern, URLResolver
from typing_extensions import NotRequired, TypedDict


class TemplatesSettingsOptions(TypedDict):
    """Templates settings options."""

    context_processors: list[str]
    loaders: list[str | tuple[str, list[str]]]
    builtins: list[str]


class TemplatesSettings(TypedDict):
    """Templates settings."""

    NAME: str
    BACKEND: str
    DIRS: NotRequired[list[str]]
    OPTIONS: NotRequired[TemplatesSettingsOptions]
    APP_DIRS: NotRequired[Optional[bool]]


class WatchDataRecord(TypedDict):
    """Watch data record."""

    provider_id: int
    country: str


class ProviderRecordType(WatchDataRecord, total=False):
    """Provider record."""

    id: int


class Trailer(TypedDict):
    """Trailer."""

    url: str
    name: str


class TrailerSitesSettings(TypedDict):
    """Trailer sites."""

    YouTube: str
    Vimeo: str


class TmdbShowListResultProcessed(TypedDict):
    """TMDB show search result processed."""

    poster_path: Optional[str]
    popularity: float
    id: int
    first_air_date: Optional[date]
    title: str
    title_original: str


class TmdbTrailer(TypedDict):
    """TMDB trailer."""

    key: str
    name: str
    site: TrailerSite


class TmdbShowProcessed(TypedDict):
    """TMDB show processed."""

    tmdb_id: int
    imdb_id: str
    first_air_date: Optional[date]
    title_original: str
    poster: Optional[str]
    homepage: Optional[str]
    trailers: list[TmdbTrailer]
    title: str
    overview: Optional[str]


class OmdbShowProcessed(TypedDict):
    """OMDb show processed."""

    writer: Optional[str]
    actors: Optional[str]
    genre: Optional[str]
    country: Optional[str]
    imdb_rating: Optional[str]


class ShowTmdbOmdb(TmdbShowProcessed, OmdbShowProcessed):
    """Show TMDb and OMDb merged together."""


TrailerSite = Literal["YouTube", "Vimeo"]
SearchType = Literal["show", "actor"]

# UntypedObject means it is a loaded JSON object
UntypedObject: TypeAlias = dict[str, Any]

URL: TypeAlias = URLPattern | URLResolver
