from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from ..models.confirmation import Confirmation
from ..models.holiday_plan import HolidayPlan
from ..models.holiday_record import HolidayRecord


def get_holiday_change_key():
    record_type = ContentType.objects.get_for_model(HolidayRecord)
    plan_type = ContentType.objects.get_for_model(HolidayPlan)

    c1 = HolidayRecord.objects.all().aggregate(count=Count("id"))["count"]
    c2 = HolidayPlan.objects.all().aggregate(count=Count("id"))["count"]
    c3 = Confirmation.objects.latest()
    if c3 is not None:
        c3 = c3.confirmed.timestamp()

    key = f"{c1}.{c2}.{c3}"
    return key
