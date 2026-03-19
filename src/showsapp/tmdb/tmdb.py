"""TMDB."""

from collections import abc
from datetime import date, datetime, time, timedelta
from typing import Optional, cast
from urllib.parse import urljoin

import requests
import tmdbsimple as tmdb
from django.conf import settings
from sentry_sdk import capture_exception

from ..exceptions import TrailerSiteNotFoundError
from ..types import (
    SearchType,
    TmdbShowListResultProcessed,
    TmdbShowProcessed,
    TmdbTrailer,
    WatchDataRecord,
)
from ..validation import validate_language
from .exceptions import TmdbInvalidSearchTypeError, TmdbNoImdbIdError
from .types import (
    TmdbCast,
    TmdbCombinedCredits,
    TmdbPerson,
    TmdbProvider,
    TmdbShow,
    TmdbShowListResult,
    TmdbWatchData,
    TmdbWatchDataCountry,
)

tmdb.API_KEY = settings.TMDB_KEY


def get_tmdb_url(tmdb_id: int) -> str:
    """Get TMDB URL."""
    return f"{settings.TMDB_SHOW_BASE_URL}{tmdb_id}/"


def get_poster_url(size: str, poster: Optional[str]) -> Optional[str]:
    """Get poster URL."""
    if size == "small":
        poster_size = settings.POSTER_SIZE_SMALL
        no_image_url = settings.NO_POSTER_SMALL_IMAGE_URL
    elif size == "normal":
        poster_size = settings.POSTER_SIZE_NORMAL
        no_image_url = settings.NO_POSTER_NORMAL_IMAGE_URL
    else:  # size == "big":
        poster_size = settings.POSTER_SIZE_BIG
        no_image_url = settings.NO_POSTER_BIG_IMAGE_URL
    if poster is not None:
        return settings.POSTER_BASE_URL + poster_size + "/" + poster
    return no_image_url


def _remove_trailing_slash_from_tmdb_poster(poster: Optional[str]) -> Optional[str]:
    """Remove trailing slash from TMDB poster."""
    if poster:
        return poster[1:]
    return None


def _filter_tv_only(entries: list[TmdbCast]) -> list[TmdbCast]:
    return [e for e in entries if e.get("media_type") == "tv"]


def _get_date(date_str: Optional[str]) -> Optional[date]:
    """Get date."""
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    return None


def _get_processed_show_data(
    entries: list[TmdbCast] | list[TmdbShowListResult],
) -> list[TmdbShowListResultProcessed]:
    """Return processed show data."""
    shows: list[TmdbShowListResultProcessed] = []
    for entry in entries:
        show: TmdbShowListResultProcessed = {
            "poster_path": _remove_trailing_slash_from_tmdb_poster(
                entry.get("poster_path")
            ),
            "popularity": entry.get("popularity", 0),
            "id": entry["id"],
            "first_air_date": _get_date(entry.get("first_air_date")),
            "title": entry.get("name", ""),
            "title_original": entry.get("original_name", ""),
        }
        shows.append(show)
    return shows


def search_shows(
    query_str: str, search_type: SearchType, lang: str
) -> list[TmdbShowListResultProcessed]:
    """
    Search Shows.

    Searches for shows based on the query string.
    For actor search - the first person found is used.
    """
    SEARCH_TYPES = ["show", "actor"]
    if search_type not in SEARCH_TYPES:
        raise TmdbInvalidSearchTypeError(search_type)

    validate_language(lang)

    query = query_str.encode("utf-8")
    params = {"query": query, "language": lang, "include_adult": settings.INCLUDE_ADULT}
    search = tmdb.Search()
    if search_type == "show":
        shows: list[TmdbShowListResult] = search.tv(**params)["results"]
        return _get_processed_show_data(shows)

    # search_type == "actor"
    persons: list[TmdbPerson] = search.person(**params)["results"]
    if persons:
        person_id = persons[0]["id"]
    else:
        return []
    person = tmdb.People(person_id)
    combined_credits: TmdbCombinedCredits = person.combined_credits(language=lang)
    cast_entries: list[TmdbCast] = _filter_tv_only(combined_credits["cast"])
    shows_processed = _get_processed_show_data(cast_entries)
    return shows_processed


def _is_valid_trailer_site(site: str) -> bool:
    """Return True if trailer site is valid."""
    return site in settings.TRAILER_SITES.keys()


def _get_trailers(tmdb_show: tmdb.TV, lang: str) -> list[TmdbTrailer]:
    """Get trailers."""
    trailers = []
    videos = tmdb_show.videos(language=lang)
    for video in videos["results"]:
        if video.get("type") == "Trailer":
            site = video["site"]
            try:
                if not _is_valid_trailer_site(site):
                    raise TrailerSiteNotFoundError(f"Site - {site}")
            except TrailerSiteNotFoundError as e:
                if settings.DEBUG:  # pragma: no cover
                    raise
                capture_exception(e)
                continue
            trailer: TmdbTrailer = {
                "name": video.get("name", "Trailer"),
                "key": video["key"],
                "site": site,
            }
            trailers.append(trailer)
    return trailers


def get_watch_data(tmdb_id: int) -> list[WatchDataRecord]:
    """Get watch data."""
    watch_data: list[WatchDataRecord] = []
    results: TmdbWatchData = tmdb.TV(tmdb_id).watch_providers()["results"]
    items: abc.ItemsView[str, TmdbWatchDataCountry] = cast(
        abc.ItemsView[str, TmdbWatchDataCountry], results.items()
    )
    for country, data in items:
        if country in settings.PROVIDERS_SUPPORTED_COUNTRIES and "flatrate" in data:
            for provider in data["flatrate"]:
                record = WatchDataRecord(
                    country=country, provider_id=provider["provider_id"]
                )
                watch_data.append(record)
    return watch_data


def _get_show_data(tmdb_show: tmdb.TV, lang: str) -> TmdbShow:
    """Get show data."""
    show: TmdbShow = tmdb_show.info(language=lang)
    return show


def _get_time_from_min(minutes: Optional[int]) -> Optional[time]:
    if minutes:
        return (datetime(1900, 1, 1) + timedelta(minutes=minutes)).time()
    return None


def get_tmdb_show_data(tmdb_id: int) -> TmdbShowProcessed:
    """Get TMDB show data."""
    tmdb_show = tmdb.TV(tmdb_id)
    show_info_en = _get_show_data(tmdb_show, lang=settings.LANGUAGE_EN)

    # Get external IDs for IMDB ID
    external_ids = tmdb_show.external_ids()
    imdb_id = external_ids.get("imdb_id")
    if not imdb_id:
        raise TmdbNoImdbIdError(tmdb_id)

    first_air_date = _get_date(show_info_en.get("first_air_date"))

    # Get runtime from episode_run_time (average)
    episode_run_times = show_info_en.get("episode_run_time", [])
    avg_runtime = episode_run_times[0] if episode_run_times else None

    return {
        "tmdb_id": tmdb_id,
        "imdb_id": imdb_id,
        "first_air_date": first_air_date,
        "title_original": show_info_en.get("original_name", ""),
        "poster": _remove_trailing_slash_from_tmdb_poster(
            show_info_en.get("poster_path")
        ),
        "homepage": show_info_en.get("homepage"),
        "trailers": _get_trailers(tmdb_show, lang=settings.LANGUAGE_EN),
        "title": show_info_en.get("name", ""),
        "overview": show_info_en.get("overview"),
        "runtime": _get_time_from_min(avg_runtime),
    }


def get_tmdb_providers() -> list[TmdbProvider]:
    """Get TMDB providers."""
    params = {"api_key": settings.TMDB_KEY}
    response = requests.get(
        urljoin(settings.TMDB_API_BASE_URL, "watch/providers/tv"),
        params=params,
        timeout=settings.REQUESTS_TIMEOUT,
    )
    providers: list[TmdbProvider] = response.json()["results"]
    return providers


def get_trending() -> list[TmdbShowListResultProcessed]:
    """Get trending shows."""
    tmdb_trending = tmdb.Trending(media_type="tv", time_window="week")
    return _get_processed_show_data(tmdb_trending.info()["results"])
