"""Update the IMDb ratings."""

from typing import Any

from django_tqdm import BaseCommand

from showsapp.models import Show
from showsapp.omdb import get_omdb_show_data


class Command(BaseCommand):
    """Update the IMDb ratings."""

    help = "Update the IMDb ratings"

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute command."""
        shows = Show.objects.all()
        tqdm = self.tqdm(total=shows.count(), unit="show")
        last_show = shows.last()
        if last_show:
            for show in shows:
                show_info = show.cli_string(last_show.pk)
                tqdm.set_description(show_info)
                show_data = get_omdb_show_data(show.imdb_id)
                new_rating = show_data["imdb_rating"]
                if new_rating:
                    old_rating = str(show.imdb_rating)
                    if old_rating != new_rating:
                        show.imdb_rating = new_rating
                        show.save()
                        message = f"{show} - rating updated"
                        tqdm.info(message)
                tqdm.update()
