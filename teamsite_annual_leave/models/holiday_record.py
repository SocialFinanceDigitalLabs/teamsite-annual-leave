from django.contrib.auth import get_user_model
from django.db import models

from .holiday_plan import HolidayPlan
from .holiday_record_type import HolidayRecordType
from .holiday_user import HolidayUser

User = get_user_model()


class HolidayRecord(models.Model):
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    start_half = models.BooleanField(default=False, null=False)
    end_half = models.BooleanField(default=False, null=False)
    adjustment = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    record_type = models.ForeignKey(
        HolidayRecordType, on_delete=models.PROTECT, null=False, blank=False
    )
    user = models.ForeignKey(
        HolidayUser,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="records",
    )
    title = models.CharField(max_length=255, null=False, default="Annual Leave")
    approved_by = models.CharField(max_length=255, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=False)
    upstream_id = models.IntegerField(
        null=True, blank=True
    )  # Used for import & synchronization
    holiday_plan = models.ForeignKey(
        HolidayPlan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="records",
    )
    created = models.DateTimeField(blank=True, auto_now_add=True)
    last_modified = models.DateTimeField(blank=True, auto_now=True)

    def __str__(self):
        adjustment = f"({self.adjustment})" if self.adjustment is not None else ""
        return (
            f"[{self.pk}] {self.start_date}/{self.end_date} {adjustment} - {self.title}"
        )
