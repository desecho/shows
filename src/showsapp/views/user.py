"""User views."""

from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import User
from ..serializers import UserPreferencesSerializer

if TYPE_CHECKING:
    from rest_framework.permissions import BasePermission


class UserCheckEmailAvailabilityView(APIView):
    """Check email availability view."""

    permission_classes: list[type["BasePermission"]] = []

    def post(self, request: Request) -> Response:
        """Return True if email is available."""
        try:
            email = request.data["email"]
        except KeyError:
            return Response(status=HTTPStatus.BAD_REQUEST)
        response = not User.objects.filter(email=email).exists()
        return Response(response)


class UserPreferencesView(APIView):
    """User preferences view."""

    def put(self, request: Request) -> Response:
        """Save preferences."""
        user: User = cast(User, request.user)
        serializer = UserPreferencesSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTPStatus.OK)

        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)

    def get(self, request: Request) -> Response:
        """Load preferences."""
        user: User = cast(User, request.user)
        serializer = UserPreferencesSerializer(user)
        return Response(serializer.data)
