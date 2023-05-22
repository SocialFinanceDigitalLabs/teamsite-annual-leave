from django.core import serializers
from django.db import models

from .holiday_record import HolidayRecord
from .holiday_user import HolidayUser


class Confirmation(models.Model):
    confirmed = models.DateTimeField(blank=True, auto_now_add=True)
    year = models.IntegerField(null=False)
    user = models.ForeignKey(
        HolidayUser,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="holiday_confirmations",
    )
    data = models.TextField(null=True)

    def save(self, *args, **kwargs):
        if self.data is None:
            records = HolidayRecord.objects.filter(user=self.user, year=self.year)
            self.data = serializers.serialize("json", records)
        super(Confirmation, self).save(*args, **kwargs)

    class Meta:
        get_latest_by = "confirmed"
