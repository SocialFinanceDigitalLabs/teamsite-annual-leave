from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from teamsite_annual_leave.models.holiday_plan import HolidayPlan
from teamsite_annual_leave.models.holiday_record import HolidayRecord
from teamsite_annual_leave.models.holiday_user import HolidayUser
from teamsite_annual_leave.util.bank_holiday_parser import (
    load_holiday_fixtures,
    synchronise_holidays,
)

User = get_user_model()


class ExportHolidaysTest(TestCase):
    fixtures = ["record-types"]

    def setUp(self) -> None:
        synchronise_holidays(load_holiday_fixtures())
        self.user = User.objects.create_user("holidayuser1")
        self.holiday_user = HolidayUser.objects.create(
            user=self.user, notes="This is a test user"
        )

    def test_normal_plan(self):
        HolidayPlan.objects.create(
            user=self.holiday_user, allowance=26, start_date="2020-01-01"
        )
        records = HolidayRecord.objects.filter(user=self.holiday_user, year=2020)

        self.assertEqual(
            records.count(), 1
        )  # We should now have one record for the initial allowance
        self.assertEqual(records.first().adjustment, 26)
        self.assertEqual(records.first().record_type.code, "ENT")

    def test_normal_plan_previous_year(self):
        HolidayPlan.objects.create(
            user=self.holiday_user, allowance=26, start_date="2019-01-01"
        )
        records = HolidayRecord.objects.filter(user=self.holiday_user, year=2020)

        self.assertEqual(
            records.count(), 1
        )  # We should now have one record for the initial allowance
        self.assertEqual(records.first().adjustment, 26)
        self.assertEqual(records.first().record_type.code, "ENT")

    def test_part_time_plan(self):
        HolidayPlan.objects.create(
            user=self.holiday_user, allowance=26, start_date="2020-01-01", mon_days=0
        )
        records = HolidayRecord.objects.filter(user=self.holiday_user, year=2020)

        self.assertEqual(records.count(), 6)
        self.assertEqual(
            records.filter(record_type__code="ENT").first().adjustment, Decimal("20.8")
        )

        self.assertEqual(sum([r.adjustment for r in records]), Decimal("23.2"))

    def test_half_day_plan(self):
        HolidayPlan.objects.create(
            user=self.holiday_user, allowance=26, start_date="2020-01-01", fri_days=0.5
        )
        records = HolidayRecord.objects.filter(user=self.holiday_user, year=2020)

        self.assertEqual(records.count(), 5)
        self.assertEqual(
            records.filter(record_type__code="ENT").first().adjustment, Decimal("23.4")
        )

        self.assertEqual(sum([r.adjustment for r in records]), Decimal("24.1"))

    def test_half_day_part_year_plan(self):
        HolidayPlan.objects.create(
            user=self.holiday_user, allowance=26, start_date="2020-01-01", fri_days=0.5
        )
        HolidayPlan.objects.create(
            user=self.holiday_user, allowance=26, start_date="2020-12-01"
        )
        records = HolidayRecord.objects.filter(
            user=self.holiday_user, year=2020
        ).order_by("start_date")

        self.assertEqual(records.count(), 7)
        self.assertEqual(
            records.filter(record_type__code="ENT").first().adjustment, Decimal("23.4")
        )

        self.assertEqual(sum([r.adjustment for r in records]), Decimal("23.8"))
