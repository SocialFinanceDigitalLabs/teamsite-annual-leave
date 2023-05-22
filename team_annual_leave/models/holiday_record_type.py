from django.db import models


class HolidayRecordType(models.Model):
    title = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True)
    system_option = models.BooleanField()

    def __str__(self):
        return self.title
