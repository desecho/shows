"""List views."""

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, prefetch_related_objects
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import List, ProviderRecord, Record, Show, User, UserAnonymous
from ..utils import generate_x_share_url
from .types import ProviderObject, ProviderRecordObject, RecordObject, ShowObject
from .utils import add_show_to_list, get_anothers_account

if TYPE_CHECKING:
    from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class ChangeRatingView(APIView):
    """Change rating view."""

    def put(self, request: Request, record_id: int) -> Response:
        """Change rating."""
        try:
            rating = int(request.data["rating"])
        except (KeyError, ValueError):
            return Response(status=HTTPStatus.BAD_REQUEST)

        if rating < 0 or rating > 5:
            return Response(status=HTTPStatus.BAD_REQUEST)

        record = get_object_or_404(Record, user=request.user, pk=record_id)
        if record.rating != rating:
            record.rating = rating
            record.save()
        return Response()


class AddToListView(APIView):
    """Add to list view."""

    def post(self, request: Request, show_id: int) -> Response:
        """Add show to list."""
        try:
            list_id = int(request.data["listId"])
        except (KeyError, ValueError):
            return Response(status=HTTPStatus.BAD_REQUEST)

        if not List.is_valid_id(list_id):
            raise Http404

        get_object_or_404(Show, pk=show_id)
        user: User = cast(User, request.user)
        add_show_to_list(show_id, list_id, user)
        return Response()


class RemoveRecordView(APIView):
    """Remove record view."""

    def delete(self, request: Request, record_id: int) -> Response:
        """Remove record."""
        record = get_object_or_404(Record, user=request.user, pk=record_id)
        record.delete()
        return Response()


class SaveCommentView(APIView):
    """Save comment view."""

    def put(self, request: Request, record_id: int) -> Response:
        """Save comment."""
        record = get_object_or_404(Record, user=request.user, pk=record_id)

        try:
            comment = request.data["comment"]
        except KeyError:
            return Response(status=HTTPStatus.BAD_REQUEST)

        if record.comment != comment:
            record.comment = comment
            record.save()
        return Response()


class ShareToSocialMediaView(APIView):
    """Share to social media view."""

    def post(self, request: Request, record_id: int) -> Response:
        """Generate social media share URL."""
        record = get_object_or_404(Record, user=request.user, pk=record_id)

        if record.list_id != List.WATCHED or (
            not record.rating and not record.comment.strip()
        ):
            return Response(
                {"error": "Only watched shows with ratings or comments can be shared"},
                status=HTTPStatus.BAD_REQUEST,
            )

        platform = request.data.get("platform", "twitter")

        if platform == "twitter":
            share_url = generate_x_share_url(record)
            return Response({"share_url": share_url})

        return Response(
            {"error": "Unsupported platform"}, status=HTTPStatus.BAD_REQUEST
        )


class RecordsView(APIView):
    """Records view."""

    anothers_account: Optional[User] = None
    permission_classes: list[type["BasePermission"]] = []

    @staticmethod
    def _sort_records(records: QuerySet[Record]) -> QuerySet[Record]:
        """Sort records."""
        return records.order_by("order", "-date")

    @staticmethod
    def _get_record_show_data(
        record_ids_and_show_ids_list: list[tuple[int, int]],
    ) -> tuple[list[int], dict[int, int]]:
        """Get record's show data."""
        show_ids = [x[1] for x in record_ids_and_show_ids_list]
        record_ids_and_show_ids = {x[0]: x[1] for x in record_ids_and_show_ids_list}
        return (show_ids, record_ids_and_show_ids)

    def _get_list_data(self, records: QuerySet[Record]) -> dict[int, int]:
        """Get list data."""
        show_ids, record_and_show_ids = self._get_record_show_data(
            list(records.values_list("id", "show_id"))
        )
        user: Union[User, UserAnonymous] = cast(
            Union[User, UserAnonymous], self.request.user
        )
        show_ids_and_list_ids_list: list[tuple[int, int]] = list(
            user.get_records()
            .filter(show_id__in=show_ids)
            .values_list("show_id", "list_id")
        )
        show_and_list_ids: dict[int, int] = {}
        for show_id, list_id in show_ids_and_list_ids_list:
            show_and_list_ids[show_id] = list_id

        list_data: dict[int, int] = {}
        for record_id, show_id in record_and_show_ids.items():
            list_data[record_id] = show_and_list_ids.get(show_id, 0)
        return list_data

    def _filter_out_provider_records_for_other_countries(
        self, provider_records: list[ProviderRecord]
    ) -> None:
        for provider_record in list(provider_records):
            user: User = cast(User, self.request.user)
            if user.country != provider_record.country:
                provider_records.remove(provider_record)

    def _get_provider_records(self, show: Show) -> list[ProviderRecord]:
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

    def _get_record_objects(self, records: QuerySet[Record]) -> list[RecordObject]:
        """Get record objects."""
        record_objects: list[RecordObject] = []
        for record in records:
            provider_records = self._get_provider_records(record.show)
            record_object: RecordObject = {
                "id": record.pk,
                "order": record.order,
                "comment": record.comment,
                "commentArea": bool(record.comment),
                "rating": record.rating,
                "providerRecords": self._get_provider_record_objects(provider_records),
                "show": self._get_show_object(record.show),
                "listId": record.list.pk,
                "additionDate": record.date.timestamp(),
            }
            record_objects.append(record_object)
        return record_objects

    def _inject_list_ids(
        self, records: QuerySet[Record], record_objects: list[RecordObject]
    ) -> None:
        list_data = self._get_list_data(records)
        for record_object in record_objects:
            record_object["listId"] = list_data.get(record_object["id"])

    @staticmethod
    def _get_records(user: Union[User, UserAnonymous]) -> QuerySet[Record]:
        """Get records for certain user."""
        return user.get_records().select_related("show")

    @staticmethod
    def _get_users() -> list["User"]:
        """Get users."""
        users = User.objects.exclude(hidden=True)
        return list(users)

    def check_if_allowed(
        self, request: Request, username: Optional[str] = None
    ) -> None:
        """Check if user is allowed to see the page."""
        if username is None and request.user.is_anonymous:
            raise Http404
        user: User = cast(User, request.user)
        if user.username == username:
            return
        self.anothers_account = get_anothers_account(username)
        if self.anothers_account:
            if User.objects.get(username=username) not in self._get_users():
                raise PermissionDenied

    def get(self, request: Request, **kwargs: Any) -> Response:
        """Get data for the list view."""
        username: Optional[str] = kwargs.get("username")
        self.check_if_allowed(request, username)
        anothers_account = self.anothers_account
        user: User = (
            cast(User, request.user) if anothers_account is None else anothers_account
        )
        records = self._get_records(user)
        records = self._sort_records(records)

        actual_user: User = cast(User, request.user)
        if actual_user.is_authenticated and actual_user.is_country_supported:
            prefetch_related_objects(list(records), "show__provider_records__provider")

        record_objects = self._get_record_objects(records)

        return Response(record_objects)


class SaveRecordsOrderView(APIView):
    """Save records order view."""

    def put(self, request: Request) -> Response:
        """Save records order."""
        try:
            records = request.data["records"]
        except KeyError:
            return Response(status=HTTPStatus.BAD_REQUEST)

        user: User = cast(User, request.user)
        for record in records:
            try:
                Record.objects.filter(pk=record["id"], user=user).update(
                    order=record["order"]
                )
            except KeyError:
                return Response(status=HTTPStatus.BAD_REQUEST)
        return Response()
