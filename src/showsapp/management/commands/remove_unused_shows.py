"""Remove unused shows."""

from typing import Any

from django_tqdm import BaseCommand

from showsapp.models import Show


class Command(BaseCommand):
    """Remove unused shows."""

    help = "Remove unused shows"

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute command."""
        shows = Show.objects.all()
        tqdm = self.tqdm(total=shows.count(), unit="show")
        last_show = shows.last()
        if last_show:
            for show in shows:
                show_info = show.cli_string(last_show.pk)
                tqdm.set_description(show_info)
                if not show.records.exists():
                    show.delete()
                    message = f"{show} removed"
                    tqdm.info(message)
                tqdm.update()
