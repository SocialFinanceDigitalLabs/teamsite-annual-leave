from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class HolidayUser(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=False, blank=False, related_name="holidays"
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
