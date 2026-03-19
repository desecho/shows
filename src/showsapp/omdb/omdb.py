"""OMDb."""

import requests
from django.conf import settings
from requests.exceptions import RequestException
from sentry_sdk import capture_exception

from ..types import OmdbShowProcessed
from .exceptions import OmdbError, OmdbLimitReachedError, OmdbRequestError
from .types import OmdbShow, OmdbShowPreprocessed, OmdbShowPreprocessedKey


def _get_processed_omdb_show_data(data_raw: OmdbShow) -> OmdbShowProcessed:
    """Get processed OMDB show data."""
    data: OmdbShowPreprocessed = {
        "Writer": None,
        "Actors": None,
        "Genre": None,
        "Country": None,
        "imdbRating": None,
    }
    items: list[tuple[OmdbShowPreprocessedKey, str]] = [
        (key, value)  # type: ignore[misc]
        for (key, value) in data_raw.items()
        if key in data and value != "N/A"
    ]
    for key, value in items:
        if len(value) > 255:
            data[key] = value[:252] + "..."
        data[key] = value
    return {
        "writer": data["Writer"],
        "actors": data["Actors"],
        "genre": data["Genre"],
        "country": data["Country"],
        "imdb_rating": data["imdbRating"],
    }


def get_omdb_show_data(imdb_id: str) -> OmdbShowProcessed:
    """Get show data from OMDB."""
    try:
        params = {"apikey": settings.OMDB_KEY, "i": imdb_id, "type": "series"}
        response = requests.get(
            settings.OMDB_BASE_URL, params=params, timeout=settings.REQUESTS_TIMEOUT
        )
    except RequestException as e:
        if settings.DEBUG:
            raise
        capture_exception(e)
        raise OmdbRequestError from e
    show_data: OmdbShow = response.json()
    show_data_response: str = show_data["Response"]
    if show_data_response == "True":
        return _get_processed_omdb_show_data(show_data)
    error = show_data["Error"]
    if error == "Request limit reached!":
        raise OmdbLimitReachedError
    raise OmdbError(error, imdb_id)
