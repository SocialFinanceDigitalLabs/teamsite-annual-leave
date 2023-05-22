from django.apps import AppConfig


class TeamsiteAnnualLeaveConfig(AppConfig):
    name = "teamsite_annual_leave"

    def ready(self):
        from .tasks.holiday_plan_tasks import holiday_receiver
