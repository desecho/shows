"""Show detail views."""

from datetime import datetime, time
from typing import TYPE_CHECKING, Any, List, Optional, cast
from urllib.parse import urljoin

from babel.dates import format_date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception

from ..models import ProviderRecord, Record, Show, User
from ..omdb import get_omdb_show_data
from ..tmdb import get_poster_url, get_tmdb_show_data, get_tmdb_url, get_watch_data
from ..utils import is_show_released
from .types import ProviderObject, ProviderRecordObject, RecordObject, ShowObject

if TYPE_CHECKING:
    from rest_framework.permissions import BasePermission


class ShowDetailView(APIView):
    """Show detail view."""

    permission_classes: list[type["BasePermission"]] = []

    def _filter_out_provider_records_for_other_countries(
        self, provider_records: list[ProviderRecord]
    ) -> None:
        """Filter out provider records for other countries."""
        for provider_record in list(provider_records):
            user: User = cast(User, self.request.user)
            if user.is_authenticated and user.country != provider_record.country:
                provider_records.remove(provider_record)

    def _get_provider_records(self, show: Show) -> list[ProviderRecord]:
        """Get provider records for show."""
        user: User = cast(User, self.request.user)
        if user.is_authenticated and user.is_country_supported and show.is_released:
            provider_records = list(show.provider_records.all())
            self._filter_out_provider_records_for_other_countries(provider_records)
            return provider_records
        return []

    @staticmethod
    def _get_provider_record_objects(
        provider_records: list[ProviderRecord],
    ) -> list[ProviderRecordObject]:
        """Get provider record objects."""
        provider_record_objects: list[ProviderRecordObject] = []
        for provider_record in provider_records:
            provider_object: ProviderObject = {
                "logo": provider_record.provider.logo,
                "name": provider_record.provider.name,
            }
            provider_record_object: ProviderRecordObject = {
                "tmdbWatchUrl": provider_record.tmdb_watch_url,
                "provider": provider_object,
            }
            provider_record_objects.append(provider_record_object)
        return provider_record_objects

    @staticmethod
    def _get_show_object(show: Show) -> ShowObject:
        """Get show object."""
        return {
            "id": show.pk,
            "title": show.title,
            "titleOriginal": show.title_original,
            "isReleased": show.is_released,
            "posterNormal": show.poster_normal,
            "posterBig": show.poster_big,
            "posterSmall": show.poster_small,
            "imdbRating": show.imdb_rating_float,
            "firstAirDate": show.first_air_date_formatted,
            "firstAirDateTimestamp": show.first_air_date_timestamp,
            "country": show.country,
            "writer": show.writer,
            "genre": show.genre,
            "actors": show.actors,
            "overview": show.overview,
            "homepage": show.homepage,
            "imdbUrl": show.imdb_url,
            "tmdbUrl": show.tmdb_url,
            "trailers": show.get_trailers(),
            "hasPoster": show.has_poster,
        }

    def _get_user_record(self, show: Show) -> Optional[RecordObject]:
        """Get user's record for this show if exists."""
        user: User = cast(User, self.request.user)
        if not user.is_authenticated:
            return None  # type: ignore[unreachable]

        try:
            record = Record.objects.select_related("show").get(user=user, show=show)
            provider_records = self._get_provider_records(record.show)
            return {
                "id": record.pk,
                "order": record.order,
                "show": self._get_show_object(record.show),
                "comment": record.comment,
                "commentArea": bool(record.comment),
                "rating": record.rating,
                "providerRecords": self._get_provider_record_objects(provider_records),
                "listId": record.list.pk,
                "additionDate": record.date.timestamp(),
            }
        except Record.DoesNotExist:
            return None

    def _create_show_object_from_tmdb(self, tmdb_id: int) -> ShowObject:
        """Create show object from TMDB data when show is not in database."""
        try:
            tmdb_data = get_tmdb_show_data(tmdb_id)

            try:
                omdb_data = get_omdb_show_data(tmdb_data["imdb_id"])
                country = omdb_data.get("country")
                writer = omdb_data.get("writer")
                genre = omdb_data.get("genre")
                actors = omdb_data.get("actors")
                imdb_rating = omdb_data.get("imdb_rating")
            except Exception as e:
                capture_exception(e)
                country = None
                writer = None
                genre = None
                actors = None
                imdb_rating = None

            first_air_date_formatted = None
            if tmdb_data["first_air_date"]:
                first_air_date_formatted = format_date(
                    tmdb_data["first_air_date"], locale=self.request.LANGUAGE_CODE
                )

            first_air_date_timestamp = 0.0
            if tmdb_data["first_air_date"]:
                dt = datetime.combine(tmdb_data["first_air_date"], time())
                first_air_date_timestamp = dt.timestamp()
            else:
                next_year = datetime.now() + relativedelta(years=1)
                first_air_date_timestamp = next_year.timestamp()

            poster_small = get_poster_url("small", tmdb_data["poster"])
            poster_normal = get_poster_url("normal", tmdb_data["poster"])
            poster_big = get_poster_url("big", tmdb_data["poster"])

            tmdb_url = get_tmdb_url(tmdb_id)
            imdb_url = urljoin(settings.IMDB_BASE_URL, tmdb_data["imdb_id"])

            return {
                "id": tmdb_id,
                "title": tmdb_data["title"],
                "titleOriginal": tmdb_data["title_original"],
                "isReleased": is_show_released(tmdb_data["first_air_date"]),
                "posterNormal": poster_normal,
                "posterBig": poster_big,
                "posterSmall": poster_small,
                "imdbRating": float(imdb_rating) if imdb_rating else None,
                "firstAirDate": first_air_date_formatted,
                "firstAirDateTimestamp": first_air_date_timestamp,
                "country": country,
                "writer": writer,
                "genre": genre,
                "actors": actors,
                "overview": tmdb_data["overview"],
                "homepage": tmdb_data["homepage"],
                "imdbUrl": imdb_url,
                "tmdbUrl": tmdb_url,
                "trailers": self._convert_tmdb_trailers_to_trailers(
                    tmdb_data["trailers"]
                ),
                "hasPoster": tmdb_data["poster"] is not None,
            }
        except Exception as e:
            capture_exception(e)
            raise Http404("Show not found on TMDB") from e

    @staticmethod
    def _convert_tmdb_trailers_to_trailers(tmdb_trailers: List[Any]) -> List[Any]:
        """Convert TMDB trailers to standard trailer format."""
        trailers = []
        for tmdb_trailer in tmdb_trailers:
            site = tmdb_trailer["site"]
            key = tmdb_trailer["key"]
            name = tmdb_trailer["name"]

            trailer_sites = dict(settings.TRAILER_SITES)
            if site in trailer_sites:
                base_url = trailer_sites[site]
                trailer_url = f"{base_url}{key}"
                trailer = {
                    "url": trailer_url,
                    "name": name,
                }
                trailers.append(trailer)
        return trailers

    @staticmethod
    def _get_tmdb_provider_records(tmdb_id: int) -> list[ProviderRecord]:
        """Get provider records from TMDB for a show not in database."""
        try:
            _ = get_watch_data(tmdb_id)
            return []
        except Exception as e:
            capture_exception(e)
            return []

    def get(self, request: Request, tmdb_id: int) -> Response:
        """Get show details by TMDB ID."""
        try:
            show = Show.objects.prefetch_related("provider_records__provider").get(
                tmdb_id=tmdb_id
            )

            provider_records = self._get_provider_records(show)
            show_object = self._get_show_object(show)
            user_record = self._get_user_record(show)

            response_data = {
                "show": show_object,
                "providerRecords": self._get_provider_record_objects(provider_records),
                "userRecord": user_record,
            }

        except Show.DoesNotExist:
            show_object = self._create_show_object_from_tmdb(tmdb_id)
            provider_records = self._get_tmdb_provider_records(tmdb_id)

            response_data = {
                "show": show_object,
                "providerRecords": self._get_provider_record_objects(provider_records),
                "userRecord": None,
            }

        return Response(response_data)
