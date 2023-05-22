from collections import OrderedDict
from decimal import Decimal

from django.db.models import Q

from ..models.confirmation import Confirmation
from ..models.holiday_plan import HolidayPlanCacheLookup
from ..models.holiday_record import HolidayRecord
from ..models.holiday_user import HolidayUser
from ..util.date import daterange


def _search_system_records(records, day):
    for r in records:
        if r.start_date <= day <= r.end_date:
            return r


def generate_holiday_report(user, year):
    try:
        user = HolidayUser.objects.get(user=user)
    except HolidayUser.DoesNotExist:
        return None

    year = int(year)

    plan_lookup = HolidayPlanCacheLookup()
    holiday_records = HolidayRecord.objects.filter(user=user, year=year).order_by(
        "start_date"
    )
    system_records = HolidayRecord.objects.filter(
        Q(user__isnull=True) & (Q(year=year) | Q(year=year + 1))
    ).order_by("start_date")

    try:
        last_confirmation = Confirmation.objects.filter(user=user, year=year).latest()
    except Confirmation.DoesNotExist:
        last_confirmation = None

    result_list = []
    allowance = 0
    rollover = 0
    public_holiday_adjustment = 0
    for record in holiday_records:
        start = record.start_date
        end = record.end_date

        item = dict(
            id=record.id,
            start=start,
            end=end,
            title=record.title,
            allowance_used=0,
            adjustment=record.adjustment,
            approved_by=record.approved_by,
        )

        if record.record_type.code == "ENT":
            allowance += record.adjustment

        if record.record_type.code == "ROL":
            rollover += record.adjustment

        if record.record_type.code == "PHADJ":
            public_holiday_adjustment += record.adjustment

        if record.record_type_id == 5:
            item["days"] = []
            for day, type in daterange(start, end):
                days_requested = 1
                if record.start_half and type[0]:
                    days_requested = 0.5
                elif record.end_half and type[1]:
                    days_requested = 0.5

                # Check for standard allowances
                plan = plan_lookup.get_for_user_and_date(user, day)
                working_hours = plan.get_days_for_day_of_week(day.weekday())
                allowance_used = Decimal(min(working_hours, days_requested))

                # Check for public holidays and office closures
                holiday_for_day = _search_system_records(system_records, day)
                if holiday_for_day is not None:
                    holiday = (
                        holiday_for_day.adjustment
                        if holiday_for_day.adjustment is not None
                        else 1
                    )
                    allowance_used = max(0, allowance_used - holiday)
                else:
                    holiday = 0

                allowance_used = Decimal(allowance_used)

                day_record = dict(
                    date=day,
                    working_hours=working_hours,
                    days_requested=days_requested,
                    public_holiday_name=holiday_for_day.title
                    if holiday_for_day is not None
                    else None,
                    public_holiday=holiday,
                    allowance_used=allowance_used,
                )
                item["days"].append(day_record)

            for day in item["days"]:
                item["allowance_used"] = item["allowance_used"] + day["allowance_used"]

        result_list.append(item)

    total_remainder = 0
    total_adjustment = 0
    total_used = 0
    for result in result_list:

        adjustment = result["adjustment"] if result["adjustment"] is not None else 0
        total_adjustment += adjustment

        allowance_used = result["allowance_used"]
        total_used += allowance_used

        total_remainder = total_remainder + adjustment - allowance_used

        result["remainder"] = total_remainder
        result["total_allowance"] = total_adjustment
        result["total_used"] = total_used

    summary = dict(
        year=year,
        allowance=allowance,
        rollover=rollover,
        public_holiday_adjustment=public_holiday_adjustment,
        total_allowance=total_adjustment,
        total_used=total_used,
        remainder=total_remainder,
        details=result_list,
    )

    # These are special rules for 2020
    month_summaries = OrderedDict()
    irregular_hours = False
    for record in result_list:
        for day in record.get("days", []):
            date = day["date"]
            allowance_used = day["allowance_used"]
            month_summaries[date.month] = (
                month_summaries.get(date.month, 0) + allowance_used
            )

            if day.get("working_hours", 1) != 1:
                irregular_hours = True

    summary["monthly_breakdown"] = month_summaries
    summary["irregular_hours"] = irregular_hours
    summary["jan_to_aug"] = sum([month_summaries.get(m, 0) for m in range(1, 9)])
    summary["allowance_minus_rollover"] = (
        allowance + rollover - 7
    )  # This is weirdness for rules - be careful

    try:
        summary["jan_to_aug_frac"] = (
            summary["jan_to_aug"] / summary["allowance_minus_rollover"]
        )
    except ZeroDivisionError:
        summary["jan_to_aug_frac"] = None

    summary["sep_to_nov"] = sum([month_summaries.get(m, 0) for m in range(9, 12)])

    if last_confirmation is not None:
        summary["last_confirmed"] = last_confirmation.confirmed

    return summary
