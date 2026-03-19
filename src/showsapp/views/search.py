"""Search views."""

import json
from http import HTTPStatus
from operator import itemgetter
from typing import TYPE_CHECKING, Optional, cast

from django.conf import settings
from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception

from ..models import List, Show, User
from ..tasks import load_and_save_watch_data_task
from ..tmdb import TmdbInvalidSearchTypeError, TmdbNoImdbIdError, search_shows
from ..types import SearchType, TmdbShowListResultProcessed
from ..utils import load_show_data
from .types import SearchOptions, ShowListResult
from .utils import (
    add_show_to_list,
    filter_out_shows_user_already_has_in_lists,
    get_show_list_result,
)

if TYPE_CHECKING:
    from rest_framework.permissions import BasePermission


class SearchShowView(APIView):
    """Search show view."""

    permission_classes: list[type["BasePermission"]] = []

    @staticmethod
    def _is_popular_show(popularity: float) -> bool:
        """Return True if show is popular."""
        return popularity >= settings.MIN_POPULARITY

    @staticmethod
    def _sort_by_date(
        shows: list[TmdbShowListResultProcessed],
    ) -> list[TmdbShowListResultProcessed]:
        """Sort shows by date."""
        shows_with_date = []
        shows_without_date = []
        for show in shows:
            if show["first_air_date"]:
                shows_with_date.append(show)
            else:
                shows_without_date.append(show)
        shows_with_date = sorted(
            shows_with_date, key=itemgetter("first_air_date"), reverse=True
        )
        shows = shows_with_date + shows_without_date
        return shows

    def _filter_out_unpopular_shows(
        self, tmdb_shows: list[TmdbShowListResultProcessed]
    ) -> None:
        for tmdb_show in list(tmdb_shows):
            if not self._is_popular_show(tmdb_show["popularity"]):
                tmdb_shows.remove(tmdb_show)

    def _get_shows_from_tmdb(
        self,
        query: str,
        search_type: SearchType,
        sort_by_date: bool,
        popular_only: bool,
    ) -> list[ShowListResult]:
        """Get shows from TMDB."""
        lang = self.request.LANGUAGE_CODE
        tmdb_shows = search_shows(query, search_type, lang)
        if sort_by_date:
            tmdb_shows = self._sort_by_date(tmdb_shows)

        if popular_only:
            self._filter_out_unpopular_shows(tmdb_shows)

        return [get_show_list_result(tmdb_show, lang) for tmdb_show in tmdb_shows]

    def get(self, request: Request) -> Response:
        """Return a list of shows based on the search query."""
        try:
            GET = request.GET
            query = GET["query"]
            options: SearchOptions = json.loads(GET["options"])
            type_ = GET["type"]
            if type_ not in ("show", "actor"):
                return Response(status=HTTPStatus.BAD_REQUEST)
            search_type: SearchType = cast(SearchType, type_)
        except KeyError:
            return Response(status=HTTPStatus.BAD_REQUEST)
        try:
            shows = self._get_shows_from_tmdb(
                query, search_type, options["sortByDate"], options["popularOnly"]
            )
        except TmdbInvalidSearchTypeError:
            return Response(status=HTTPStatus.BAD_REQUEST)
        if request.user.is_authenticated:
            user: User = request.user
            filter_out_shows_user_already_has_in_lists(shows, user)
        shows = shows[: settings.MAX_RESULTS]
        return Response(shows)


class AddToListFromDbView(APIView):
    """Add to list from DB view."""

    @staticmethod
    def add_show_to_db(tmdb_id: int) -> int:
        """Add a show to the database. Return show ID."""
        show_data = load_show_data(tmdb_id)
        show = Show(**show_data)
        show.save()
        if show.is_released:
            load_and_save_watch_data_task.delay(show.pk)
        return show.pk

    @staticmethod
    def _get_show_id(tmdb_id: int) -> Optional[int]:
        """Get show ID. Return show ID or None if show is not found."""
        try:
            show: Show = Show.objects.get(tmdb_id=tmdb_id)
            return show.pk
        except Show.DoesNotExist:
            return None

    def _add_to_list_from_db(
        self, show_id: Optional[int], tmdb_id: int, list_id: int, user: User
    ) -> bool:
        """Add a show to a list from database. Return True on success."""
        if show_id is None:
            try:
                show_id = self.add_show_to_db(tmdb_id)
            except TmdbNoImdbIdError as e:
                capture_exception(e)
                return False

        if list_id == List.WATCHED:
            show = Show.objects.get(pk=show_id)
            if not show.is_released:
                return False

        add_show_to_list(show_id, list_id, user)
        return True

    def post(self, request: Request) -> Response:
        """Add a show to a list."""
        try:
            tmdb_id = int(request.data["showId"])
            list_id = int(request.data["listId"])
        except (KeyError, ValueError):
            return Response(status=HTTPStatus.BAD_REQUEST)

        if not List.is_valid_id(list_id):
            raise Http404

        show_id = self._get_show_id(tmdb_id)
        user: User = cast(User, request.user)
        result = self._add_to_list_from_db(show_id, tmdb_id, list_id, user)
        if not result:
            if list_id == List.WATCHED:
                try:
                    if show_id:
                        show = Show.objects.get(pk=show_id)
                        if not show.is_released:
                            return Response(
                                {"status": "unreleased"}, status=HTTPStatus.BAD_REQUEST
                            )
                except Show.DoesNotExist:
                    pass
            return Response({"status": "not_found"})
        return Response()
