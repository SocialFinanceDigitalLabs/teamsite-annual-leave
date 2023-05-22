from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from teamsite_annual_leave.util.bank_holiday_parser import (
    load_holiday_fixtures,
    synchronise_holidays,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Synchronizes bank holidays from the fixtures file"

    def add_arguments(self, parser):
        parser.add_argument("--fixtures-file", type=str)
        parser.add_argument("--testrun", action="store_true")

    def handle(self, *args, fixtures_file, testrun, **options):
        synchronise_holidays(
            load_holiday_fixtures(fixtures_file=fixtures_file), testrun=testrun
        )
