"""AI Recommendations view."""

from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Dict, Optional, cast

import tmdbsimple as tmdb
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception

from ..models import List, User
from ..openai.client import OpenAIClient
from ..openai.exceptions import OpenAIError
from ..openai.types import RecommendationRequest, RecommendationResponse
from ..types import TmdbShowListResultProcessed
from .types import ShowListResult
from .utils import filter_out_shows_user_already_has_in_lists, get_show_list_result

tmdb.API_KEY = settings.TMDB_KEY

if TYPE_CHECKING:
    from rest_framework.permissions import BasePermission


def _get_tmdb_show_from_imdb_id(imdb_id: str) -> Optional[TmdbShowListResultProcessed]:
    """Get TMDB show data from IMDB ID."""
    try:
        find = tmdb.Find(imdb_id)
        results = find.info(external_source="imdb_id")

        tv_results = results.get("tv_results", [])
        if not tv_results:
            return None

        show = tv_results[0]

        first_air_date = None
        if show.get("first_air_date"):
            try:
                first_air_date = datetime.strptime(
                    show["first_air_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                first_air_date = None

        return TmdbShowListResultProcessed(
            id=show["id"],
            title=show["name"],
            title_original=show["original_name"],
            poster_path=show["poster_path"],
            first_air_date=first_air_date,
            popularity=show["popularity"],
        )
    except (KeyError, ValueError, TypeError):
        return None


class RecommendationsView(APIView):
    """AI Recommendations view."""

    permission_classes: list[type["BasePermission"]] = [IsAuthenticated]

    @staticmethod
    def _parse_year_range(
        year_start: Optional[str], year_end: Optional[str]
    ) -> Optional[Dict[str, int]]:
        """Parse year range parameters."""
        if not year_start or not year_end:
            return None
        try:
            return {"start": int(year_start), "end": int(year_end)}
        except ValueError as exc:
            raise ValueError("Invalid year range values") from exc

    @staticmethod
    def _parse_min_rating(min_rating: Optional[str]) -> Optional[int]:
        """Parse minimum rating parameter."""
        if not min_rating:
            return None
        try:
            min_rating_int = int(min_rating)
            if not settings.AI_MIN_RATING <= min_rating_int <= settings.AI_MAX_RATING:
                raise ValueError(
                    f"Minimum rating must be between {settings.AI_MIN_RATING} "
                    f"and {settings.AI_MAX_RATING}"
                )
            return min_rating_int
        except ValueError as exc:
            if "must be between" in str(exc):
                raise
            raise ValueError("Invalid minimum rating value") from exc

    @staticmethod
    def _parse_recommendations_number(
        recommendations_number: Optional[str],
    ) -> Optional[int]:
        """Parse recommendations number parameter."""
        if not recommendations_number:
            return None
        try:
            recommendations_number_int = int(recommendations_number)
            min_recs = settings.AI_MIN_RECOMMENDATIONS
            max_recs = settings.AI_MAX_RECOMMENDATIONS
            if not min_recs <= recommendations_number_int <= max_recs:
                raise ValueError(
                    f"Number of recommendations must be between {min_recs} and {max_recs}"
                )
            return recommendations_number_int
        except ValueError as exc:
            if "must be between" in str(exc):
                raise
            raise ValueError("Invalid recommendations number value") from exc

    @staticmethod
    def _get_user_show_preferences(
        user: User,
    ) -> tuple[list[str], list[str], list[str]]:
        """Get user's liked, disliked, and unrated shows based on ratings."""
        liked_records = user.records.filter(
            list_id=List.WATCHED, rating__gte=3
        ).select_related("show")
        liked_shows = [record.show.title for record in liked_records]

        disliked_records = user.records.filter(
            list_id=List.WATCHED, rating__lte=2, rating__gt=0
        ).select_related("show")
        disliked_shows = [record.show.title for record in disliked_records]

        unrated_records = user.records.filter(
            list_id=List.WATCHED, rating=0
        ).select_related("show")
        unrated_shows = [record.show.title for record in unrated_records]

        return liked_shows, disliked_shows, unrated_shows

    @staticmethod
    def _convert_recommendations_to_shows(
        recommendations: RecommendationResponse, lang: str
    ) -> list[ShowListResult]:
        """Convert IMDB recommendations to show list results."""
        shows = []
        for recommendation in recommendations:
            try:
                tmdb_show = _get_tmdb_show_from_imdb_id(recommendation["imdb_id"])
                if tmdb_show:
                    show_result = get_show_list_result(tmdb_show, lang)
                    shows.append(show_result)
            except (KeyError, ValueError, TypeError) as exc:
                capture_exception(exc)
                continue
        return shows

    def get(self, request: Request) -> Response:
        """Return AI-generated show recommendations based on user preferences."""
        try:
            preferred_genre = request.GET.get("preferredGenre")
            year_start = request.GET.get("yearStart")
            year_end = request.GET.get("yearEnd")
            min_rating = request.GET.get("minRating")
            recommendations_number = request.GET.get("recommendationsNumber")

            try:
                year_range = self._parse_year_range(year_start, year_end)
                min_rating_int = self._parse_min_rating(min_rating)
                recommendations_number_int = self._parse_recommendations_number(
                    recommendations_number
                )
            except ValueError as exc:
                return Response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

            user = cast(User, request.user)
            liked_shows, disliked_shows, unrated_shows = (
                self._get_user_show_preferences(user)
            )

            recommendation_request = RecommendationRequest(
                liked_shows=liked_shows or None,
                disliked_shows=disliked_shows or None,
                unrated_shows=unrated_shows or None,
                preferred_genre=preferred_genre,
                year_range=year_range,
                min_rating=min_rating_int,
                recommendations_number=recommendations_number_int
                or settings.AI_MAX_RECOMMENDATIONS,
            )

            try:
                openai_client = OpenAIClient()
                recommendations = openai_client.get_show_recommendations(
                    recommendation_request
                )
            except OpenAIError as exc:
                capture_exception(exc)
                return Response(
                    {
                        "error": "Failed to get AI recommendations. Please try again later."
                    },
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            shows = RecommendationsView._convert_recommendations_to_shows(
                recommendations, request.LANGUAGE_CODE
            )
            filter_out_shows_user_already_has_in_lists(shows, user)

            return Response(shows)

        except (AttributeError, TypeError, KeyError) as exc:
            capture_exception(exc)
            return Response(
                {"error": "An unexpected error occurred"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
