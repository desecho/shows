"""Custom DRF renderers."""

from typing import Any
from zoneinfo import ZoneInfo

from django_countries.fields import Country
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder


class CountryJSONEncoder(JSONEncoder):
    """JSON encoder that serializes Country and ZoneInfo objects as strings."""

    def default(self, obj: Any) -> Any:
        """Return a JSON-serializable representation, handling Country and ZoneInfo."""
        if isinstance(obj, Country):
            return str(obj)
        if isinstance(obj, ZoneInfo):
            return getattr(obj, "key", str(obj))
        return super().default(obj)


class CountryJSONRenderer(JSONRenderer):
    """JSON renderer using the Country/ZoneInfo-aware encoder."""

    encoder_class = CountryJSONEncoder
