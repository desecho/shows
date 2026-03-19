"""OpenAI integration type definitions."""

from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict

from django.conf import settings


@dataclass
class RecommendationRequest:
    """Request structure for show recommendations."""

    liked_shows: Optional[List[str]] = None
    disliked_shows: Optional[List[str]] = None
    unrated_shows: Optional[List[str]] = None
    preferred_genre: Optional[str] = None
    year_range: Optional[Dict[str, int]] = None
    min_rating: Optional[int] = None
    recommendations_number: Optional[int] = settings.AI_MAX_RECOMMENDATIONS


@dataclass
class ShowRecommendation:
    """Single show recommendation."""

    title: str
    description: str
    confidence_score: Optional[float] = None


@dataclass
class IMDbItem(TypedDict):
    """Represents an IMDb item with its identifier."""

    imdb_id: str


RecommendationResponse = List[IMDbItem]
