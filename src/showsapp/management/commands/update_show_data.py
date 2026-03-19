"""Update show data."""

from typing import Any, Optional

from django.core.management.base import CommandParser
from django_tqdm import BaseCommand

from showsapp.models import Show
from showsapp.tmdb import TmdbNoImdbIdError
from showsapp.utils import load_show_data


class Command(BaseCommand):
    """Update show data."""

    help = """Update all show data except for IMDb ratings and watch data.

    If one argument is used then the show with the selected show_id is updated.
    If no arguments are used - all shows get updated.
    """

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments."""
        parser.add_argument("show_id", nargs="?", default=None, type=int)
        parser.add_argument(
            "-s",
            action="store_true",
            dest="start_from_id",
            default=False,
            help="Start running the script from provided show id",
        )

    @staticmethod
    def _update_show_data(show: Show) -> bool:
        """Return if the show was updated or not."""
        show_data = load_show_data(show.tmdb_id)
        # We create a new dict here to avoid modifying the original dict which would result in an error
        show_data_to_update = dict(show_data)
        # Use filter here to be able to use "update" functionality.
        # We will always have only one show.
        shows = Show.objects.filter(pk=show.pk)
        show_initial_data = shows.values()[0]
        show_data_to_update.pop("imdb_rating")
        shows.update(**show_data_to_update)
        show_updated_data = Show.objects.filter(pk=show.pk).values()[0]
        updated: bool = show_initial_data != show_updated_data
        return updated

    def handle(
        self,
        *args: Any,
        **options: Any,
    ) -> None:
        """Execute command."""
        show_id: Optional[int] = options["show_id"]
        start_from_id: bool = options["start_from_id"]
        shows = Show.filter(show_id, start_from_id)
        shows_total = shows.count()
        # We don't want a progress bar if we just have one show to process
        disable = shows_total == 1
        if not shows:  # In case show_id is too high and we don't get any shows
            if start_from_id:
                self.error(f"There are no shows with IDs > {show_id}", fatal=True)
            else:
                # Assume we have at least one show in the DB
                self.error(f"There is no show with ID {show_id}", fatal=True)

        tqdm = self.tqdm(total=shows_total, unit="shows", disable=disable)
        last_show = shows.last()
        if last_show:
            for show in shows:
                show_info = show.cli_string(last_show.pk)
                tqdm.set_description(show_info)
                try:
                    result = self._update_show_data(show)
                except TmdbNoImdbIdError:
                    tqdm.error(f'"{show.title_with_id}" is not found in IMDb')
                else:
                    updated = result
                    if updated:
                        tqdm.info(f'"{show}" is updated')
                tqdm.update()
