"""OpenAI client for show recommendations."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.conf import settings
from openai import OpenAI

from .exceptions import OpenAIConfigurationError, OpenAIError
from .types import RecommendationRequest, RecommendationResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a TV show recommendation expert.

Provide personalized TV show recommendations based on the user's preferences and viewing history. Output only a plain JSON array of objects with the following structure, without markdown or extra explanation:

[
    {
        "imdb_id": "tt1234567"
    }
]

The list should contain ONLY IMDb IDs of recommended TV shows, NOT the titles. Each show should be relevant to the user's preferences, avoiding duplicates and ensuring variety in genre and style.
The list should contain TV shows ONLY. Movies or other media should not be included.
Include both streaming-only releases (Netflix/Prime/Apple/etc.) as well as broadcast TV shows.

Recommendation logic:
- If the user has no specific preferences, recommend popular and critically acclaimed TV shows.
- Avoid recommending shows the user has already seen.
- Use disliked or liked shows to refine suggestions.
- Treat neutral/unrated shows as viewing history, not preference indicators.
- If a minimum rating is specified, all recommendations must meet or exceed it.
- If a preferred year range is given, restrict recommendations to that range.
- If preferred genres are specified, prioritize them.
- If the user requests a specific number of shows, return exactly that many.
- If genre is not specified, ensure diversity in genre and style.
- Always aim to match user preferences while introducing some variety.

IMPORTANT: Do NOT ask any questions or seek clarification. Give the results to your best ability. If there are no suitable recommendations, return at least something - you can relax user's preferences in this case.
"""

MIN_YEAR = 1928  # The year of the first TV broadcast


class OpenAIClient:
    """Client for OpenAI API interactions."""

    def __init__(self) -> None:
        """Initialize OpenAI client with API key from settings."""
        if not settings.OPENAI_API_KEY:
            raise OpenAIConfigurationError(
                "OPENAI_API_KEY is not configured in settings"
            )

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def get_show_recommendations(
        self, user_preferences: RecommendationRequest
    ) -> RecommendationResponse:
        """Get show recommendations based on user preferences."""
        logger.info("Starting show recommendation request")
        logger.debug("User preferences: %s", user_preferences)
        try:
            logger.debug("Validating user preferences")
            OpenAIClient._validate_user_preferences(user_preferences)

            logger.debug("Building recommendation prompt")
            prompt = OpenAIClient._build_recommendation_prompt(user_preferences)
            logger.debug("Generated prompt: %s", prompt)

            logger.info("Calling OpenAI API with model: %s", self.model)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=settings.OPENAI_MAX_TOKENS,
            )
            logger.info("OpenAI API call completed successfully")
            logger.info("Raw response received from OpenAI - %s", response)

            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI API returned empty content")
                raise OpenAIError("OpenAI API returned empty content")

            logger.debug("Raw OpenAI response: %s", content)
            logger.debug("Parsing recommendation response")
            parsed_content = OpenAIClient._parse_recommendation_response(content)

            logger.debug("Filtering out duplicate IMDb IDs")
            original_count = len(parsed_content)
            self._filter_out_duplicated_ids(parsed_content)
            final_count = len(parsed_content)

            if original_count != final_count:
                logger.info(
                    "Filtered out %d duplicate recommendations",
                    original_count - final_count,
                )

            logger.info("Successfully generated %d show recommendations", final_count)
            return parsed_content

        except Exception as e:
            logger.error("Error during show recommendation: %s", str(e), exc_info=True)
            if hasattr(e, "__module__") and "openai" in e.__module__:
                raise OpenAIError(f"OpenAI API error: {str(e)}") from e
            raise OpenAIError(f"Unexpected error: {str(e)}") from e

    @staticmethod
    def _convert_rating(rating: float) -> float:
        """Convert a 5-star rating to a 10-star rating."""
        return rating * 2

    @staticmethod
    def _validate_user_preferences(preferences: RecommendationRequest) -> None:
        """Validate user preferences against settings constraints."""
        OpenAIClient._validate_recommendations_number(
            preferences.recommendations_number
        )
        OpenAIClient._validate_rating(preferences.min_rating)
        OpenAIClient._validate_show_list(preferences.liked_shows, "liked")
        OpenAIClient._validate_show_list(preferences.disliked_shows, "disliked")
        OpenAIClient._validate_show_list(preferences.unrated_shows, "unrated")
        OpenAIClient._validate_genre(preferences.preferred_genre)
        OpenAIClient._validate_year_range(preferences.year_range)

    @staticmethod
    def _validate_recommendations_number(recommendations_number: Optional[int]) -> None:
        """Validate recommendations number."""
        if recommendations_number is not None:
            if (
                not settings.AI_MIN_RECOMMENDATIONS
                <= recommendations_number
                <= settings.AI_MAX_RECOMMENDATIONS
            ):
                raise ValueError(
                    f"Number of recommendations must be between {settings.AI_MIN_RECOMMENDATIONS} "
                    f"and {settings.AI_MAX_RECOMMENDATIONS}"
                )

    @staticmethod
    def _validate_rating(min_rating: Optional[int]) -> None:
        """Validate rating."""
        if min_rating is not None:
            if not settings.AI_MIN_RATING <= min_rating <= settings.AI_MAX_RATING:
                raise ValueError(
                    f"Minimum rating must be between {settings.AI_MIN_RATING} "
                    f"and {settings.AI_MAX_RATING}"
                )

    @staticmethod
    def _validate_show_list(shows: Optional[List[str]], show_type: str) -> None:
        """Validate show list (liked or disliked)."""
        if shows is not None:
            for show in shows:
                if not isinstance(show, str):
                    raise ValueError(f"All {show_type} shows must be strings")
                if len(show.strip()) == 0:
                    raise ValueError(
                        f"{show_type.capitalize()} show titles cannot be empty"
                    )
                if len(show) > settings.AI_MAX_SHOW_TITLE_LENGTH:
                    raise ValueError(
                        f"{show_type.capitalize()} show title '{show[:50]}...' exceeds maximum length of "
                        f"{settings.AI_MAX_SHOW_TITLE_LENGTH} characters"
                    )

    @staticmethod
    def _validate_genre(preferred_genre: Optional[str]) -> None:
        """Validate preferred genre."""
        if preferred_genre is not None:
            all_valid_genres = settings.MAIN_GENRES + settings.SUBGENRES
            if preferred_genre not in all_valid_genres:
                raise ValueError(
                    f"Preferred genre '{preferred_genre}' is not valid. "
                    f"Valid genres are: {', '.join(all_valid_genres)}"
                )

    @staticmethod
    def _validate_year_range(year_range: Optional[Dict[str, int]]) -> None:
        """Validate year range."""
        if year_range is None:
            return

        if not isinstance(year_range, dict):
            raise ValueError(
                "Year range must be a dictionary with 'start' and 'end' keys"
            )

        if "start" not in year_range or "end" not in year_range:
            raise ValueError("Year range must contain both 'start' and 'end' keys")

        start_year = year_range["start"]
        end_year = year_range["end"]

        if not isinstance(start_year, int) or not isinstance(end_year, int):
            raise ValueError("Year range values must be integers")

        if start_year > end_year:
            raise ValueError("Start year cannot be greater than end year")

        current_year = datetime.now().year
        if start_year < MIN_YEAR or end_year > current_year:
            raise ValueError(
                f"Year range must be between {MIN_YEAR} and {current_year}"
            )

    @staticmethod
    def _build_recommendation_prompt(preferences: RecommendationRequest) -> str:
        """Build the prompt for show recommendations."""
        prompt_parts = ["Recommend TV shows based on the following user preferences:"]

        if preferences.liked_shows:
            liked_shows_str = ", ".join(preferences.liked_shows)
            prompt_parts.append(f"Shows they liked: {liked_shows_str}")

        if preferences.disliked_shows:
            disliked_shows_str = ", ".join(preferences.disliked_shows)
            prompt_parts.append(f"Shows they disliked: {disliked_shows_str}")

        if preferences.unrated_shows:
            unrated_shows_str = ", ".join(preferences.unrated_shows)
            prompt_parts.append(
                f"Shows they watched but didn't rate (neutral): {unrated_shows_str}"
            )

        if preferences.preferred_genre:
            prompt_parts.append(f"Preferred genre: {preferences.preferred_genre}")

        if preferences.year_range:
            prompt_parts.append(
                f"Preferred year range: {preferences.year_range['start']}-{preferences.year_range['end']}"
            )

        if preferences.min_rating:
            min_rating = OpenAIClient._convert_rating(preferences.min_rating)
            prompt_parts.append(f"Minimum rating: {min_rating}/10")

        if preferences.recommendations_number:
            prompt_parts.append(
                f"Number of recommendations: {preferences.recommendations_number}"
            )
        else:
            prompt_parts.append(
                f"Number of recommendations: {settings.AI_MAX_RECOMMENDATIONS}"
            )

        return "\n\n".join(prompt_parts)

    @staticmethod
    def _parse_recommendation_response(content: str) -> RecommendationResponse:
        """Parse the OpenAI response into structured data."""
        try:
            parsed_data = json.loads(content.strip())
            if not isinstance(parsed_data, list):
                raise ValueError("Expected a list of recommendations")

            for item in parsed_data:
                if not isinstance(item, dict) or "imdb_id" not in item:
                    raise ValueError("Each recommendation must have an 'imdb_id' field")

            return parsed_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}") from e

    @staticmethod
    def _filter_out_duplicated_ids(recommendations: RecommendationResponse) -> None:
        """Remove duplicate IMDb IDs from recommendations list in-place."""
        seen_ids = set()
        filtered_recommendations = []

        for item in recommendations:
            imdb_id = item.get("imdb_id")
            if imdb_id and imdb_id not in seen_ids:
                seen_ids.add(imdb_id)
                filtered_recommendations.append(item)

        recommendations.clear()
        recommendations.extend(filtered_recommendations)
