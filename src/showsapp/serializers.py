"""Serializers."""

from typing import Any

from django_countries import countries
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from .models import User


class UserPreferencesSerializer(serializers.ModelSerializer[User]):
    """User preferences serializer."""

    country = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        """Meta."""

        model = User
        fields = ["hidden", "country"]

    @staticmethod
    def validate_country(value: str | None) -> str | None:
        """Validate country field."""
        if not value:
            return value

        if value not in dict(countries):
            raise ValidationError(f"'{value}' is not a valid country code.")

        return value

    def to_representation(self, instance: User) -> dict[str, Any]:
        """Convert country field to string representation."""
        data = super().to_representation(instance)
        data["country"] = str(instance.country) if instance.country else None
        return data
