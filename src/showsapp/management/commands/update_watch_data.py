"""Update watch data."""

import sys
from typing import Any, Optional, cast

from django.conf import settings
from django.core.management.base import CommandParser
from django.db.models import QuerySet
from django_tqdm import BaseCommand
from sentry_sdk import capture_exception

from showsapp.exceptions import ProviderNotFoundError
from showsapp.models import List, ProviderRecord, Record, Show
from showsapp.tmdb import get_watch_data
from showsapp.types import ProviderRecordType, WatchDataRecord


class Command(BaseCommand):
    """Update watch data."""

    help = """Update watch data.

    If one argument is provided then the show with the selected show_id is updated.
    It is updated even if the show does not need to be updated (was recently updated).

    If no arguments are provided - all shows get updated.
    """

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments."""
        parser.add_argument("show_id", nargs="?", default=None, type=int)
        parser.add_argument(
            "-m",
            action="store_true",
            dest="minimal",
            default=False,
            help=(
                'Update only minimal watch data. It updates only watch data for shows that are in "To Watch" '
                "list, is released, and only if a show is in a list of a user who's country is supported"
            ),
        )

    @staticmethod
    def _filter_out_shows_not_requiring_update(shows: list[Show]) -> None:
        """
        Filter out shows that don't need an update.

        Remove shows that don't need an update from `shows`.
        """
        for show in list(shows):
            if show.is_watch_data_updated_recently:
                shows.remove(show)

    @staticmethod
    def _remove_no_longer_available_provider_records(
        existing_provider_records: list[ProviderRecordType],
        watch_data: list[WatchDataRecord],
    ) -> bool:
        """Remove provider records that are no longer available."""
        removed = False
        for provider_record in existing_provider_records:
            provider_record_id = provider_record.pop("id")
            # Remove the record if it's no longer available.
            if provider_record not in watch_data:
                ProviderRecord.objects.get(pk=provider_record_id).delete()
                removed = True
        return removed

    @staticmethod
    def _filter_out_already_existing_provider_records(
        existing_provider_records: list[ProviderRecordType],
        watch_data: list[WatchDataRecord],
    ) -> None:
        """
        Filter out already existing provider records.

        Remove already existing provider records from `watch_data`.
        """
        for provider_record in existing_provider_records:
            if provider_record in watch_data:
                # Don't create a record if it already exists.
                watch_data.remove(provider_record)

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute command."""
        show_id: Optional[int] = options["show_id"]
        minimal: bool = options["minimal"]
        if minimal and not show_id:
            records: QuerySet[Record] = Record.objects.filter(
                list_id=List.TO_WATCH,
                show__first_air_date__isnull=False,
                user__country__isnull=False,
            )
            shows = list(
                set(
                    record.show
                    for record in records
                    if record.show.is_released and record.user.is_country_supported
                )
            )
        else:
            if show_id is not None:
                try:
                    Show.objects.get(pk=show_id)
                except Show.DoesNotExist:
                    self.error(f"There is no show with ID {show_id}", fatal=True)
            shows = list(Show.filter(show_id, first_air_date__isnull=False))
            # If show_id is provided, we force update the show
            # (we ignore if the show needs an update or not).
            if show_id is None:
                self._filter_out_shows_not_requiring_update(shows)

        shows_total = len(shows)
        # We don't want a progress bar if we just have one show to process
        disable = shows_total == 1
        if not shows:
            self.info("No shows to update")
            sys.exit()

        tqdm = self.tqdm(total=shows_total, unit="show", disable=disable)
        last_show = Show.last()
        if last_show:
            for show in shows:
                show_info = show.cli_string(last_show.pk)
                tqdm.set_description(show_info)
                watch_data = get_watch_data(show.tmdb_id)
                if not watch_data:
                    tqdm.error(f"No watch data obtained for {show}. Skipping.")
                    tqdm.update()
                    continue

                existing_provider_records = show.provider_records.all().values(
                    "id", "provider_id", "country"
                )
                removed = self._remove_no_longer_available_provider_records(
                    cast(list[ProviderRecordType], list(existing_provider_records)),
                    watch_data,
                )
                self._filter_out_already_existing_provider_records(
                    cast(
                        list[ProviderRecordType],
                        list(
                            existing_provider_records.values("provider_id", "country")
                        ),
                    ),
                    watch_data,
                )
                try:
                    show.save_watch_data(watch_data)
                except ProviderNotFoundError as e:
                    if settings.DEBUG:
                        raise
                    capture_exception(e)
                if watch_data or removed:
                    message = f"{show} - watch data updated"
                    tqdm.info(message)
                tqdm.update()
