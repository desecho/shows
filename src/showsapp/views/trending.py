"""Trending view."""

from typing import TYPE_CHECKING

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import User
from ..tmdb import get_trending
from .utils import filter_out_shows_user_already_has_in_lists, get_show_list_result

if TYPE_CHECKING:
    from rest_framework.permissions import BasePermission


class TrendingView(APIView):
    """Trending view."""

    permission_classes: list[type["BasePermission"]] = []

    def get(self, request: Request) -> Response:
        """Return a list of trending shows."""
        tmdb_shows = get_trending()
        shows = [
            get_show_list_result(tmdb_show, request.LANGUAGE_CODE)
            for tmdb_show in tmdb_shows
        ]
        if request.user.is_authenticated:
            user: User = request.user
            filter_out_shows_user_already_has_in_lists(shows, user)
        return Response(shows)
