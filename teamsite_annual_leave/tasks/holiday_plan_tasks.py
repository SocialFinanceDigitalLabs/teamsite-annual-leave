from datetime import date

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..models.holiday_plan import WEEKDAYS, HolidayPlan, HolidayPlanCacheLookup
from ..models.holiday_record import HolidayRecord
from ..models.holiday_record_type import HolidayRecordType
from ..models.holiday_user import HolidayUser


@receiver([post_save, post_delete], sender=HolidayRecord)
@receiver([post_save, post_delete], sender=HolidayPlan)
def holiday_receiver(sender, instance, **kwargs):
    if sender == HolidayPlan:
        year_list = (
            HolidayRecord.objects.filter(record_type__code__in=("PH", "CLS"))
            .values("year")
            .distinct()
        )
        for year in year_list:
            recalculate_plans(instance.user, year["year"])


def recalculate_plans(user, year):
    plan_lookup = HolidayPlanCacheLookup()
    plans = plan_lookup.get_for_user(user)
    if len(plans) == 0:
        return

    with transaction.atomic():
        type_entitlement = HolidayRecordType.objects.get(code="ENT")
        type_public_holiday = HolidayRecordType.objects.get(code="PH")
        type_public_holiday_adjustment = HolidayRecordType.objects.get(code="PHADJ")

        for p in plans:
            p.records.filter(year=year).delete()

        dt = date(year, 1, 1)
        p = plan_lookup.get_for_user_and_date(user, dt)
        if p is not None and p.allowance > 0 and p.start_date != dt:
            HolidayRecord.objects.create(
                user=p.user,
                start_date=dt,
                end_date=dt,
                year=dt.year,
                adjustment=p.outstanding_allowance_at_date(dt),
                title=f"Entitlement Year Start {dt.year}",
                record_type=type_entitlement,
                holiday_plan=p,
            )
            if p.week_sum < 5:
                public_holiday_count = HolidayRecord.objects.filter(
                    record_type=type_public_holiday, year=year
                ).count()
                ph_correction = (
                    p.week_sum / 5 * public_holiday_count
                ) - public_holiday_count
                HolidayRecord.objects.create(
                    user=p.user,
                    start_date=dt,
                    end_date=dt,
                    year=dt.year,
                    adjustment=ph_correction,
                    title=f"Bank Holiday Adjustment Year Start {dt.year}",
                    record_type=type_public_holiday_adjustment,
                    holiday_plan=p,
                )

    for p in plans:
        dt = p.start_date
        if dt.year == year:
            plan_type = "New Plan" if p.allowance > 0 else "Leaving"
            HolidayRecord.objects.create(
                user=p.user,
                start_date=dt,
                end_date=dt,
                year=dt.year,
                adjustment=p.outstanding_allowance_at_date(dt),
                title=f"Entitlement Year {dt.year} - {plan_type}",
                record_type_id=1,
                holiday_plan_id=p.pk,
            )
            if p.week_sum < 5:
                public_holiday_count = HolidayRecord.objects.filter(
                    record_type=type_public_holiday, year=dt.year
                ).count()
                ph_correction = (
                    p.week_sum / 5 * public_holiday_count
                ) - public_holiday_count
                HolidayRecord.objects.create(
                    user=p.user,
                    start_date=dt,
                    end_date=dt,
                    year=dt.year,
                    adjustment=p.pro_rata_remainder_at_date(dt, ph_correction),
                    title=f"Bank Holiday Adjustment Year {dt.year} - New Plan",
                    record_type=type_public_holiday_adjustment,
                    holiday_plan=p,
                )

        dt = p.end_date
        if dt is not None and dt.year == year:
            HolidayRecord.objects.create(
                user=p.user,
                start_date=dt,
                end_date=dt,
                year=dt.year,
                adjustment=-p.outstanding_allowance_at_date(dt),
                title=f"Entitlement Year {dt.year} - End Plan",
                record_type_id=1,
                holiday_plan_id=p.pk,
            )
            if p.week_sum < 5:
                public_holiday_count = HolidayRecord.objects.filter(
                    record_type=type_public_holiday, year=dt.year
                ).count()
                ph_correction = (
                    p.week_sum / 5 * public_holiday_count
                ) - public_holiday_count
                HolidayRecord.objects.create(
                    user=p.user,
                    start_date=dt,
                    end_date=dt,
                    year=dt.year,
                    adjustment=-p.pro_rata_remainder_at_date(dt, ph_correction),
                    title=f"Bank Holiday Adjustment Year {dt.year} - End Plan",
                    record_type=type_public_holiday_adjustment,
                    holiday_plan=p,
                )

    for ph in HolidayRecord.objects.filter(record_type__code="PH", year=year):
        day_of_week = ph.start_date.weekday()
        field = f"{WEEKDAYS[day_of_week]}_days"

        p = plan_lookup.get_for_user_and_date(user, ph.start_date)
        if p is not None:
            adjustment = 1 - getattr(p, field)
            if adjustment > 0:
                HolidayRecord.objects.create(
                    user=p.user,
                    start_date=ph.start_date,
                    end_date=ph.start_date,
                    year=ph.start_date.year,
                    adjustment=adjustment,
                    title=f"{ph.title} Adjustment",
                    record_type=type_public_holiday_adjustment,
                    holiday_plan_id=p.pk,
                )


def recalculate_all_plans():
    year_list = (
        HolidayRecord.objects.filter(record_type__code__in=("PH", "CLS"))
        .values("year")
        .distinct()
    )
    for user in HolidayUser.objects.all():
        for year in year_list:
            recalculate_plans(user, year["year"])
