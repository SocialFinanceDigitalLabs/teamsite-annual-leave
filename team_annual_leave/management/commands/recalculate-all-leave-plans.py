from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from team_annual_leave.tasks.holiday_plan_tasks import recalculate_all_plans

User = get_user_model()


class Command(BaseCommand):
    help = "Recalculate all holiday entitlements"

    def handle(self, *args, **options):
        recalculate_all_plans()
