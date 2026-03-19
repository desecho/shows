"""OMDb types."""

from __future__ import annotations

from typing import Literal, Optional

from typing_extensions import NotRequired, TypedDict

from ..types import UntypedObject


class OmdbShow(TypedDict):
    """OMDb show."""

    Title: str
    Year: str
    Rated: str
    Released: str
    Runtime: str
    Genre: str
    Writer: str
    Actors: str
    Plot: str
    Language: str
    Country: str
    Awards: str
    Poster: str
    Ratings: list[UntypedObject]
    Metascore: str
    imdbRating: str
    imdbVotes: str
    imdbID: str
    Type: str
    totalSeasons: str
    Response: str
    Error: NotRequired[str]


class OmdbShowPreprocessed(TypedDict):
    """OMDb show preprocessed."""

    Writer: Optional[str]
    Actors: Optional[str]
    Genre: Optional[str]
    Country: Optional[str]
    imdbRating: Optional[str]


OmdbShowPreprocessedKey = Literal["Writer", "Actors", "Genre", "Country", "imdbRating"]
