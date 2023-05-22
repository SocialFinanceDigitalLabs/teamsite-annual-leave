from datetime import date
from decimal import Decimal

import django.test
from django.contrib.auth import get_user_model

from teamsite_annual_leave.models.holiday_plan import HolidayPlan
from teamsite_annual_leave.models.holiday_user import HolidayUser

User = get_user_model()


class HolidayPlanTestCase(django.test.TestCase):
    fixtures = ["record-types"]

    def setUp(self):
        user1 = User.objects.create(username="user1")
        user2 = User.objects.create(username="user2")

        user1 = HolidayUser.objects.create(user=user1)
        user2 = HolidayUser.objects.create(user=user2)

        HolidayPlan.objects.create(user=user1, start_date="2020-01-01", allowance=25)
        HolidayPlan.objects.create(user=user2, start_date="2020-01-01", allowance=25)

        HolidayPlan.objects.create(user=user1, start_date="2020-05-01", allowance=27)
        HolidayPlan.objects.create(
            user=user1, start_date="2020-09-01", allowance=27, wed_days=0
        )

    def test_sequence(self):
        user1 = HolidayUser.objects.get(user__username="user1")

        plan1 = HolidayPlan.objects.for_date(user1, "2020-02-01")
        self.assertEqual(plan1.start_date, date.fromisoformat("2020-01-01"))
        self.assertEqual(plan1.end_date, date.fromisoformat("2020-04-30"))

        plan2 = plan1.next
        self.assertIsNotNone(plan2)
        self.assertEqual(plan2.previous, plan1)

        plan3 = plan2.next
        self.assertIsNotNone(plan3)
        self.assertEqual(plan3.previous, plan2)
        self.assertIsNone(plan3.next)

    def test_end_allowance(self):
        plan = HolidayPlan(start_date=date(2020, 1, 1), allowance=Decimal(25))
        self.assertEqual(plan.outstanding_allowance_at_date(date(2020, 1, 1)), 25)
        self.assertAlmostEqual(
            plan.outstanding_allowance_at_date(date(2020, 2, 1)),
            Decimal(22.9),
            places=1,
        )
        self.assertAlmostEqual(
            plan.outstanding_allowance_at_date(date(2020, 3, 1)),
            Decimal(20.9),
            places=1,
        )
        self.assertAlmostEqual(
            plan.outstanding_allowance_at_date(date(2020, 4, 1)),
            Decimal(18.8),
            places=1,
        )
        self.assertEqual(plan.outstanding_allowance_at_date(date(2020, 12, 31)), 0)

    def test_weighted_end_allowance(self):
        plan = HolidayPlan(
            start_date=date(2020, 1, 1), allowance=Decimal(25), wed_days=0
        )
        self.assertEqual(plan.outstanding_allowance_at_date(date(2020, 1, 1)), 20)
        self.assertAlmostEqual(
            plan.outstanding_allowance_at_date(date(2020, 2, 1)),
            Decimal(18.3),
            places=1,
        )
        self.assertAlmostEqual(
            plan.outstanding_allowance_at_date(date(2020, 3, 1)),
            Decimal(16.7),
            places=1,
        )
        self.assertAlmostEqual(
            plan.outstanding_allowance_at_date(date(2020, 4, 1)),
            Decimal(15.0),
            places=1,
        )
        self.assertEqual(plan.outstanding_allowance_at_date(date(2020, 12, 31)), 0)

    def test_annual_combined(self):
        """
        The purpose of this test is that if someone has two plans in a year, the total still is the same
        :return:
        """
        user1 = HolidayUser.objects.get(user__username="user1")
        plan1 = HolidayPlan.objects.for_date(user1, "2020-02-01")
        plan2 = plan1.next

        total = (
            plan1.outstanding_allowance_at_date(date(2020, 1, 1))
            - plan1.outstanding_allowance_at_end
            + plan2.outstanding_allowance_at_date(plan2.start_date)
        )

        self.assertAlmostEqual(total, Decimal(26.3), places=1)

        plan2.allowance = 25
        plan2.save()

        total = (
            plan1.outstanding_allowance_at_date(date(2020, 1, 1))
            - plan1.outstanding_allowance_at_end
            + plan2.outstanding_allowance_at_date(plan2.start_date)
        )

        self.assertAlmostEqual(total, 25, places=1)

    def test_get_for_date(self):
        user1 = HolidayUser.objects.get(user__username="user1")

        plan = HolidayPlan.objects.for_date(user1, "2019-12-31")
        self.assertIsNone(plan)

        plan = HolidayPlan.objects.for_date(user1, "2020-01-01")
        self.assertIsNotNone(plan)
