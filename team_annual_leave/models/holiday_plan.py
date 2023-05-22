from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import models

from .holiday_user import HolidayUser

User = get_user_model()

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class HolidayPlanManager(models.Manager):
    def for_date(self, user, on_date):
        return (
            self.model.objects.filter(user=user, start_date__lte=on_date)
            .order_by("start_date")
            .last()
        )


class HolidayPlan(models.Model):
    user = models.ForeignKey(
        HolidayUser,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="holiday_plans",
    )
    start_date = models.DateField(blank=False, null=False)

    allowance = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )

    mon_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=1
    )
    tue_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=1
    )
    wed_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=1
    )
    thu_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=1
    )
    fri_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=1
    )
    sat_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=0
    )
    sun_days = models.DecimalField(
        max_digits=3, decimal_places=2, null=False, default=0
    )

    created = models.DateTimeField(blank=True, auto_now_add=True)
    last_modified = models.DateTimeField(blank=True, auto_now=True)

    @property
    def next(self):
        return (
            HolidayPlan.objects.filter(user=self.user, start_date__gt=self.start_date)
            .order_by("start_date")
            .first()
        )

    @property
    def previous(self):
        return (
            HolidayPlan.objects.filter(user=self.user, start_date__lt=self.start_date)
            .order_by("start_date")
            .last()
        )

    def get_days_for_day_of_week(self, day_of_week: int):
        field_name = f"{WEEKDAYS[day_of_week]}_days"
        return getattr(self, field_name)

    @property
    def end_date(self):
        if not self.next:
            return None
        return self.next.start_date - timedelta(days=1)

    @property
    def days_as_list(self):
        values = []
        for day_of_week in WEEKDAYS:
            field_name = f"{day_of_week}_days"
            values.append(getattr(self, field_name))
        return values

    @property
    def week_sum(self):
        return sum(self.days_as_list)

    @property
    def weighted_allowance(self):
        return self.allowance * self.week_sum / 5

    def pro_rata_remainder_at_date(self, on_date, amount):
        if on_date is None:
            return None

        year_start_date = date(on_date.year, 1, 1)
        year_end_date = date(on_date.year, 12, 31)
        days_in_year = int((year_end_date - year_start_date) / timedelta(days=1))

        plan_start_date = self.start_date
        if plan_start_date.year != on_date.year:
            plan_start_date = year_start_date

        days_for_plan = int((year_end_date - plan_start_date) / timedelta(days=1))
        days_at_start = int((plan_start_date - year_start_date) / timedelta(days=1))

        allowance_for_start = amount * days_for_plan / days_in_year

        if on_date == plan_start_date:
            return allowance_for_start

        days = int((year_end_date - on_date) / timedelta(days=1))

        return allowance_for_start * days / (days_in_year - days_at_start)

    def outstanding_allowance_at_date(self, on_date):
        return self.pro_rata_remainder_at_date(on_date, self.weighted_allowance)

    @property
    def outstanding_allowance_at_end(self):
        return self.outstanding_allowance_at_date(self.end_date + timedelta(days=1))

    objects = HolidayPlanManager()

    class Meta:
        unique_together = ["user", "start_date"]


class HolidayPlanCacheLookup:
    """
    Utility for looking up plans in an efficient way
    """

    def __init__(self):
        self.plan_cache = dict()
        self.user_cache = dict()

    def __get_user__(self, user):
        resolved_user = self.user_cache.get(user)
        if resolved_user is not None:
            return resolved_user

        if isinstance(user, HolidayUser):
            resolved_user = user
        elif isinstance(user, User):
            resolved_user = HolidayUser.objects.get(user=user)
        else:
            resolved_user = HolidayUser.objects.get(user__username__iexact=user)

        self.user_cache[user] = resolved_user
        return resolved_user

    def get_for_user(self, user):
        user = self.__get_user__(user)
        plans = self.plan_cache.get(user)
        if plans is None:
            plans = HolidayPlan.objects.filter(user=user).order_by("-start_date")
            self.plan_cache[user] = plans
        return plans

    def get_for_user_and_date(self, user, date):
        plans = self.get_for_user(user)
        for p in plans:
            if p.start_date <= date:
                return p

        return None
