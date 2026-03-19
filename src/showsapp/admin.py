"""Admin."""

from typing import Optional

from django.conf import settings
from django.contrib.admin import ModelAdmin, register, site
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django_celery_results.models import GroupResult

from .models import List, Provider, ProviderRecord, Record, Show, User


@register(Record)
class RecordAdmin(ModelAdmin[Record]):
    """Record admin."""

    list_display = ("user", "show", "list", "date")
    search_fields = (
        "show__title",
        "user__username",
        "user__first_name",
        "user__last_name",
    )


@register(Show)
class ShowAdmin(ModelAdmin[Show]):
    """Show admin."""

    list_display = ("title",)
    search_fields = ("title",)


@register(ProviderRecord)
class ProviderRecordAdmin(ModelAdmin[ProviderRecord]):
    """Provider record admin."""

    list_display = ("provider", "show", "country")
    search_fields = ("show__title",)


@register(List)
class ListAdmin(ModelAdmin[List]):
    """List admin."""

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[List] = None
    ) -> bool:
        """Return True if the user has delete permission."""
        return False


@register(Provider)
class ProviderAdmin(ModelAdmin[Provider]):
    """Provider admin."""

    list_display = ("name",)
    search_fields = ("name",)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Provider] = None
    ) -> bool:
        """Return True if the user has delete permission."""
        return False


@register(User)
class UserAdmin(ModelAdmin[User]):
    """User admin."""

    list_display = ("username", "first_name", "last_name", "country")
    search_fields = ("username", "first_name", "last_name", "country")


site.unregister(Group)
if settings.IS_CELERY_DEBUG:  # pragma: no cover
    site.unregister(GroupResult)
