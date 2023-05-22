from datetime import date
from math import ceil

import reversion
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from holiday.models.holiday_plan import HolidayPlanCacheLookup
from holiday.models.holiday_record import HolidayRecord
from holiday.models.holiday_record_type import HolidayRecordType
from holiday.util.holiday_export import get_user_reports

User = get_user_model()


def populate_record(record, year, rollover_amount):
    record.end_date = record.start_date
    record.year = record.start_date.year
    record.title = f"Rollover {year} -> {year+1}"
    record.adjustment = rollover_amount
    record.comment = f"Rollover calculated {timezone.now()}"


def add_rollovers(year, users=None, max_rollover=5):
    new_years_eve = date(year, 12, 31)
    new_years_day = date(year + 1, 1, 1)
    rollover_type = HolidayRecordType.objects.get(code="ROL")

    HolidayRecord.objects.filter(
        Q(record_type=rollover_type)
        & (Q(start_date=new_years_day) | Q(start_date=new_years_eve))
    ).delete()

    users = User.objects.filter(holidays__isnull=False).order_by("username")
    reports = get_user_reports(users, year)
    plan_lookup = HolidayPlanCacheLookup()

    for report in reports:
        user = report[0]
        remainder = report[1].get("remainder", 0)
        remainder_rounded = ceil(remainder * 2) / 2

        rollover_amount = min(remainder_rounded, max_rollover)

        plan = plan_lookup.get_for_user_and_date(user, new_years_day)
        if plan.allowance == 0:
            rollover_amount = 0

        if rollover_amount > 0:
            end_record = HolidayRecord()
            end_record.user = user.holidays
            end_record.start_date = new_years_eve
            end_record.record_type = rollover_type

            start_record = HolidayRecord()
            start_record.user = user.holidays
            start_record.start_date = new_years_day
            start_record.record_type = rollover_type

            populate_record(end_record, year, -rollover_amount)
            populate_record(start_record, year, rollover_amount)

            # Declare a new revision block.
            with reversion.create_revision():
                end_record.save()
                start_record.save()

                # Store some meta-information.
                reversion.set_comment("Automatically created rollover allowances")
