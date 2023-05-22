from django.apps import AppConfig


class TeamAnnualLeaveConfig(AppConfig):
    name = "team_annual_leave"

    def ready(self):
        from .tasks.holiday_plan_tasks import holiday_receiver
