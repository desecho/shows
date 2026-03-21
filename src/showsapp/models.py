"""Models."""

import json
from datetime import datetime, time, timedelta
from typing import Any, Optional
from urllib.parse import urljoin

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    JSONField,
    Manager,
    Model,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    QuerySet,
    TextField,
    TimeField,
    UniqueConstraint,
    URLField,
)
from django.http import HttpRequest
from django.utils import formats
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from timezone_field import TimeZoneField

from .exceptions import ProviderNotFoundError
from .tmdb import get_poster_url, get_tmdb_url
from .types import TmdbTrailer, Trailer, TrailerSite, WatchDataRecord
from .utils import is_show_released


class UserBase:
    """User base class."""

    def get_show_ids(self) -> list[int]:
        """Get show IDs."""
        return list(self.get_records().values_list("show__pk", flat=True))

    def get_records(self) -> QuerySet["Record"]:
        """Get records."""
        if self.is_authenticated:  # type: ignore
            records: QuerySet[Record] = self.records.all()  # type: ignore
            return records
        return Record.objects.none()

    def get_record(self, id_: int) -> "Record":
        """Get record."""
        return self.get_records().get(pk=id_)


class User(AbstractUser, UserBase):
    """User class."""

    only_for_friends = BooleanField(
        verbose_name=_("Only for friends"),
        default=False,
        help_text=_("Show my lists only to friends"),
    )
    hidden = BooleanField(
        verbose_name=_("Hide account"),
        default=False,
        help_text=_("Don't show my lists to anybody"),
    )
    language = CharField(
        max_length=2,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        verbose_name=_("Language"),
    )
    loaded_initial_data = BooleanField(default=False)
    country = CountryField(verbose_name=_("Country"), null=True, blank=True)
    timezone = TimeZoneField(default=settings.TIME_ZONE)

    class Meta:
        """Meta options for User model."""

        app_label = "showsapp"

    def __str__(self) -> str:
        """Return string representation."""
        if self.username and not self.username.isnumeric():
            return self.username
        return self.get_full_name()

    def _get_shows_number(self, list_id: int) -> int:
        """Get shows number."""
        return self.get_records().filter(list_id=list_id).count()

    @property
    def shows_watched_number(self) -> int:
        """Get shows watched number."""
        return self._get_shows_number(List.WATCHED)

    @property
    def shows_watching_number(self) -> int:
        """Get shows watching number."""
        return self._get_shows_number(List.WATCHING)

    @property
    def shows_to_watch_number(self) -> int:
        """Get shows to watch number."""
        return self._get_shows_number(List.TO_WATCH)

    @property
    def is_country_supported(self) -> bool:
        """Return True if country is supported."""
        return self.country in settings.PROVIDERS_SUPPORTED_COUNTRIES


class UserAnonymous(AnonymousUser, UserBase):
    """Anonymous user class."""

    # Not sure if it is needed.
    def __init__(self, request: HttpRequest):
        """Init."""
        super().__init__()


class List(Model):
    """List."""

    WATCHED = 1
    WATCHING = 2
    TO_WATCH = 3
    name = CharField(max_length=255, unique=True)
    key_name = CharField(max_length=255, db_index=True, unique=True)

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.name)

    @classmethod
    def is_valid_id(cls, list_id: int) -> bool:
        """Return True if list ID is valid."""
        return list_id in [cls.WATCHED, cls.WATCHING, cls.TO_WATCH]


class Show(Model):
    """Show."""

    title = CharField(max_length=255)
    title_original = CharField(max_length=255)
    country = CharField(max_length=255, null=True, blank=True)
    overview = TextField(null=True, blank=True)
    writer = CharField(max_length=255, null=True, blank=True)
    genre = CharField(max_length=255, null=True, blank=True)
    actors = CharField(max_length=255, null=True, blank=True)
    imdb_id = CharField(max_length=15, unique=True, db_index=True)
    tmdb_id = PositiveIntegerField(unique=True)
    imdb_rating = DecimalField(max_digits=2, decimal_places=1, null=True)
    poster = CharField(max_length=255, null=True)
    first_air_date = DateField(null=True)
    homepage = URLField(null=True, blank=True)
    trailers = JSONField(null=True, blank=True)
    watch_data_update_date = DateTimeField(null=True, blank=True)

    class Meta:
        """Meta."""

        ordering = ["pk"]

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.title)

    @property
    def first_air_date_formatted(self) -> Optional[str]:
        """Return first air date formatted."""
        if self.first_air_date:
            return formats.date_format(self.first_air_date, "DATE_FORMAT")
        return None

    @property
    def first_air_date_timestamp(self) -> float:
        """Return first air date timestamp."""
        if self.first_air_date:
            dt = datetime.combine(self.first_air_date, time())
            return dt.timestamp()
        next_year = now() + relativedelta(years=1)
        return next_year.timestamp()

    @property
    def imdb_rating_float(self) -> Optional[float]:
        """Get IMDb rating float."""
        if self.imdb_rating:
            return float(self.imdb_rating)
        return None

    @property
    def imdb_url(self) -> str:
        """Return IMDb URL."""
        return urljoin(settings.IMDB_BASE_URL, self.imdb_id)

    @property
    def tmdb_url(self) -> str:
        """Return TMDB URL."""
        return get_tmdb_url(self.tmdb_id)

    @property
    def is_released(self) -> bool:
        """Return True if show is released."""
        return is_show_released(self.first_air_date)

    @property
    def is_watch_data_updated_recently(self) -> bool:
        """Return True if watch data was updated recently."""
        return (
            self.watch_data_update_date is not None
            and self.watch_data_update_date
            >= now() - timedelta(days=settings.WATCH_DATA_UPDATE_MIN_DAYS)
        )

    # Hack to make tests work
    @staticmethod
    def _get_real_trailers(trailers: list[TmdbTrailer]) -> list[TmdbTrailer]:
        """Get "real" trailers."""
        trailers_real = trailers
        if settings.IS_TEST:
            trailers_str: str = trailers  # type: ignore
            trailers_real = json.loads(trailers_str)
        return trailers_real

    def _pre_get_trailers(self) -> list[TmdbTrailer]:
        """Pre-get trailers."""
        if self.trailers:
            trailers = self._get_real_trailers(self.trailers)
            return trailers
        trailers = self._get_real_trailers(self.trailers)  # type: ignore
        return trailers

    @staticmethod
    def _get_trailer_url(site: TrailerSite, key: str) -> str:
        """Get trailer URL."""
        TRAILER_SITES = settings.TRAILER_SITES
        base_url = TRAILER_SITES[site]
        return f"{base_url}{key}"

    def get_trailers(self) -> list[Trailer]:
        """Get trailers."""
        trailers: list[Trailer] = []
        for t in self._pre_get_trailers():
            trailer: Trailer = {
                "url": self._get_trailer_url(t["site"], t["key"]),
                "name": t["name"],
            }
            trailers.append(trailer)
        return trailers

    def save_watch_data(self, watch_data: list[WatchDataRecord]) -> None:
        """Save watch data for a show."""
        for provider_record in watch_data:
            provider_id = provider_record["provider_id"]
            try:
                provider = Provider.objects.get(pk=provider_id)
            except Provider.DoesNotExist as e:
                raise ProviderNotFoundError(f"Provider ID - {provider_id}") from e
            ProviderRecord.objects.create(
                provider=provider, show=self, country=provider_record["country"]
            )
        self.watch_data_update_date = now()
        self.save()

    @classmethod
    def filter(
        cls, show_id: Optional[int], start_from_id: bool = False, **kwargs: Any
    ) -> QuerySet["Show"]:
        """Filter shows."""
        shows = cls.objects.filter(**kwargs)
        if show_id is not None:
            if start_from_id:
                return shows.filter(pk__gte=show_id)
            return shows.filter(pk=show_id)
        return shows

    def _get_poster(self, size: str) -> Optional[str]:
        """Get poster."""
        return get_poster_url(size, self.poster)

    @property
    def poster_normal(self) -> Optional[str]:
        """Get normal poster."""
        return self._get_poster("normal")

    @property
    def poster_small(self) -> Optional[str]:
        """Get small poster."""
        return self._get_poster("small")

    @property
    def poster_big(self) -> Optional[str]:
        """Get big poster."""
        return self._get_poster("big")

    @property
    def has_poster(self) -> bool:
        """Return True if show has poster."""
        return self.poster is not None

    @property
    def title_with_id(self) -> str:
        """Get title with ID."""
        return f"{self.pk} - {self}"

    @classmethod
    def last(cls) -> Optional["Show"]:
        """Get last show."""
        return cls.objects.last()

    def cli_string(self, last_show_id: int) -> str:
        """Return string representation for CLI."""
        MAX_CHARS = 40
        ENDING = ".."
        n = len(str(last_show_id)) + 1
        id_format = f"{{0: < {n}}}"
        title = str(self)
        title = (title[:MAX_CHARS] + ENDING) if len(title) > MAX_CHARS else title
        id_ = id_format.format(self.pk)
        title_max_length = MAX_CHARS + len(ENDING)
        title_format = f"{{:{title_max_length}s}}"
        title = title_format.format(title)
        return f"{id_} - {title}"[1:]


class RecordQuerySet(QuerySet["Record"]):
    """Record query set."""

    def update(self, **kwargs: Any) -> int:
        """Update records."""
        ids = self.values_list("pk", flat=True)
        rows = super().update(**kwargs)
        for id_ in ids:
            Record.objects.get(pk=id_).save()
        return rows


class Record(Model):
    """Record."""

    user = ForeignKey(User, CASCADE, related_name="records")
    show = ForeignKey(Show, CASCADE, related_name="records")
    list = ForeignKey(List, CASCADE)
    rating = PositiveSmallIntegerField(default=0)
    order = PositiveSmallIntegerField(default=0)
    comment = CharField(max_length=255, default="")
    date = DateTimeField(auto_now_add=True)
    objects: Manager["Record"] = RecordQuerySet.as_manager()

    class Meta:
        """Meta."""

        constraints = [
            UniqueConstraint(fields=("user", "show"), name="unique_user_show_record"),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.user} - {self.show.title} - {self.list}"


class Provider(Model):
    """Provider."""

    id = PositiveSmallIntegerField(primary_key=True)
    name = CharField(max_length=255)

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.name)

    @property
    def logo(self) -> str:
        """Return logo."""
        return f"/img/providers/{self.id}.jpg"


class ProviderRecord(Model):
    """Provider record."""

    provider = ForeignKey(Provider, CASCADE)
    show = ForeignKey(Show, CASCADE, related_name="provider_records")
    country = CountryField(verbose_name=_("Country"))

    class Meta:
        """Meta."""

        constraints = [
            UniqueConstraint(
                fields=("provider", "show", "country"),
                name="unique_provider_show_country_record",
            ),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.provider} - {self.show}"

    @property
    def tmdb_watch_url(self) -> str:
        """Return TMDb watch URL."""
        return f"{self.show.tmdb_url}watch?locale={self.country}"
