from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q
from tablib import Dataset

from teamsite_annual_leave.models.holiday_record import HolidayRecord

User = get_user_model()


class Command(BaseCommand):
    help = """
    Import holidays from a spreadsheet. Looks for the following columns:
      * email - the email address of the user to import holidays for. If not found, row is skipped. 
      * start_date - the start date of the holiday. If not found, row is skipped. 
      * end_date - the end date of the holiday. If not found, assume start_date.
      * start_half - if the start date is a half day. If not found, assumes False.
      * end_half - if the end date is a half day. If not found, assumes False.
      * year - the year this should be logged against. Takes the year of the start date if not found.
      * deleted - the record will be removed if this matched exactly "DELETE"
    """

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str)

    def handle(self, *args, filename, **options):
        with open(filename, "rb") as fh:
            imported_data = Dataset().load(fh, headers=True)

        imported_data.headers = [h.lower().strip() for h in imported_data.headers]

        for r in imported_data.dict:
            self.import_row(r)

    def import_row(self, row):
        if row.get("email") is None or row.get("start_date") is None:
            print("Skipping", row)
            return

        email = row.get("email")

        user = User.objects.filter(
            Q(email=email)
            | Q(additional_emails__email=email)
            | Q(username__iexact=email)
            | Q(email__icontains=email)
        ).get()

        start_date = row.get("start_date")
        end_date = (
            row.get("end_date") if row.get("end_date") is not None else start_date
        )
        start_half = True if row.get("start_half", "") != "" else False
        end_half = True if row.get("end_half", "") != "" else False
        year = row.get("year") if row.get("year") is not None else start_date.year

        holiday, created = HolidayRecord.objects.get_or_create(
            user=user,
            start_date=start_date,
            record_type_id=5,  # Annual Leave
            defaults={
                "end_date": end_date,
                "start_half": start_half,
                "end_half": end_half,
                "year": int(year),
            },
        )
        if row.get("deleted") == "DELETED":
            holiday.delete()
            print("Deleted", user, holiday)
        else:
            holiday.end_date = end_date
            holiday.start_half = start_half
            holiday.end_half = end_half
            holiday.year = int(year)
            holiday.save()
            print("Processed", user, holiday, "Added" if created else "Updated")
