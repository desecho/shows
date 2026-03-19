"""Utils for views."""

from datetime import date, datetime
from typing import Optional

from babel.dates import format_date
from django.shortcuts import get_object_or_404

from ..models import Record, User
from ..tmdb import get_poster_url, get_tmdb_url
from ..types import TmdbShowListResultProcessed
from ..utils import is_show_released
from .types import ShowListResult


def add_show_to_list(show_id: int, list_id: int, user: User) -> None:
    """Add show to list."""
    records = user.get_records().filter(show_id=show_id)
    if records.exists():
        record = records[0]
        if record.list_id != list_id:
            record.list_id = list_id
            record.date = datetime.today()
            record.save()
    else:
        record = Record(show_id=show_id, list_id=list_id, user=user)
        record.save()


def get_anothers_account(username: Optional[str]) -> Optional[User]:
    """Get another's account."""
    if username:
        return get_object_or_404(User, username=username)
    return None


def _format_date(date_: Optional[date], lang: str) -> Optional[str]:
    """Format date."""
    if date_:
        return format_date(date_, locale=lang)
    return None


def get_show_list_result(
    tmdb_show: TmdbShowListResultProcessed, lang: str
) -> ShowListResult:
    """Get show list result from TMDB show list result processed."""
    poster = tmdb_show["poster_path"]
    tmdb_id = tmdb_show["id"]
    first_air_date = tmdb_show["first_air_date"]
    return ShowListResult(
        id=tmdb_id,
        tmdbLink=get_tmdb_url(tmdb_id),
        firstAirDate=_format_date(first_air_date, lang),
        title=tmdb_show["title"],
        titleOriginal=tmdb_show["title_original"],
        poster=get_poster_url("normal", poster),
        poster2x=get_poster_url("big", poster),
        isReleased=is_show_released(first_air_date),
    )


def filter_out_shows_user_already_has_in_lists(
    shows: list[ShowListResult], user: User
) -> None:
    """Filter out shows user already has in lists."""
    user_shows_tmdb_ids = list(
        user.get_records().values_list("show__tmdb_id", flat=True)
    )
    for show in list(shows):
        if show["id"] in user_shows_tmdb_ids:
            shows.remove(show)
