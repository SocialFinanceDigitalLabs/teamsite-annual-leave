from django.core.management import BaseCommand

from team_annual_leave.tasks.add_rollovers import add_rollovers


class Command(BaseCommand):
    help = "Adds rollover for year"

    def add_arguments(self, parser):
        parser.add_argument("year", type=int)
        parser.add_argument("--max", type=int, default=5)

    def handle(self, *args, year, max, **options):
        add_rollovers(year, max_rollover=max)
