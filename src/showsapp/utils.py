"""Utils."""

from datetime import date
from typing import TYPE_CHECKING, Optional
from urllib.parse import quote

from .omdb import get_omdb_show_data
from .tmdb import get_tmdb_show_data
from .types import OmdbShowProcessed, ShowTmdbOmdb, TmdbShowProcessed

if TYPE_CHECKING:
    from .models import Record


def merge_show_data(
    show_data_tmdb: TmdbShowProcessed, show_data_omdb: OmdbShowProcessed
) -> ShowTmdbOmdb:
    """Merge show data from TMDB and OMDb together."""
    return {
        "tmdb_id": show_data_tmdb["tmdb_id"],
        "imdb_id": show_data_tmdb["imdb_id"],
        "first_air_date": show_data_tmdb["first_air_date"],
        "title_original": show_data_tmdb["title_original"],
        "poster": show_data_tmdb["poster"],
        "homepage": show_data_tmdb["homepage"],
        "trailers": show_data_tmdb["trailers"],
        "title": show_data_tmdb["title"],
        "overview": show_data_tmdb["overview"],
        "runtime": show_data_tmdb["runtime"],
        "writer": show_data_omdb["writer"],
        "actors": show_data_omdb["actors"],
        "genre": show_data_omdb["genre"],
        "country": show_data_omdb["country"],
        "imdb_rating": show_data_omdb["imdb_rating"],
    }


def load_show_data(tmdb_id: int) -> ShowTmdbOmdb:
    """Load show data from TMDB and OMDb."""
    show_data_tmdb = get_tmdb_show_data(tmdb_id)
    show_data_omdb = get_omdb_show_data(show_data_tmdb["imdb_id"])
    return merge_show_data(show_data_tmdb, show_data_omdb)


def is_show_released(first_air_date: Optional[date]) -> bool:
    """Return True if the show is released."""
    return first_air_date is not None and first_air_date <= date.today()


def generate_social_share_text(record: "Record") -> str:
    """Generate social media share text for a show record."""
    show = record.show

    year = ""
    if show.first_air_date:
        year = f" ({show.first_air_date.year})"

    share_text = (
        f"Just watched {show.title}{year} and rated it {record.rating}/5 stars!"
    )

    if record.comment.strip():
        share_text += f"\n{record.comment}"

    clean_title = "".join(c for c in show.title if c.isalnum())
    share_text += f"\n#TVShows #ShowReview #{clean_title}"

    return share_text


def generate_x_share_url(record: "Record") -> str:
    """Generate X (Twitter) share URL for a show record."""
    share_text = generate_social_share_text(record)
    encoded_text = quote(share_text)
    return f"https://twitter.com/intent/tweet?text={encoded_text}"
