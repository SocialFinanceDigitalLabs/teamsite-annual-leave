import logging
from datetime import date
from math import ceil

from django.contrib import admin
from threadlocals.threadlocals import get_request_variable, set_request_variable

from .models.confirmation import Confirmation
from .models.holiday_plan import HolidayPlan
from .models.holiday_record import HolidayRecord
from .models.holiday_record_type import HolidayRecordType
from .models.holiday_user import HolidayUser
from .util.holiday_report import generate_holiday_report

logger = logging.getLogger(__name__)


class InlineHolidayPlanAdmin(admin.TabularInline):
    model = HolidayPlan
    extra = 0
    ordering = ("-start_date",)


class InlineHolidayRecordAdmin(admin.TabularInline):
    fields = ("title", "start_date", "end_date", "adjustment", "record_type")
    readonly_fields = ("title", "start_date", "end_date", "adjustment", "record_type")
    model = HolidayRecord
    extra = 0
    ordering = ("-start_date",)


def _get_summary(user):
    varname = f"holiday_summary__{user.pk}"
    try:
        summary = get_request_variable(varname, use_threadlocal_if_no_request=False)
    except RuntimeError:
        logger.warning(
            "Threadlocal middleware may not be installed. See README for details on how to speed up requests."
        )
        summary = None

    if summary is None:
        summary = generate_holiday_report(user.user, date.today().year)
        try:
            set_request_variable(varname, summary, use_threadlocal_if_no_request=False)
        except RuntimeError:
            pass
    return summary


@admin.register(HolidayUser)
class HolidayUserAdmin(admin.ModelAdmin):
    list_display = (
        "fullname",
        "fte",
        "fte_allowance",
        "allowance",
        "rollover",
        "public_holiday_adjustment",
        "total_allowance",
        "total_used",
        "remainder",
        "allowance_minus_rollover",
        "jan_to_aug",
        "jan_to_aug_frac",
        "sep_to_nov",
        "notes",
    )
    ordering = ("user__username",)
    search_fields = ("user__username",)
    list_per_page = 25

    inlines = (InlineHolidayPlanAdmin, InlineHolidayRecordAdmin)

    def fullname(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def fte_allowance(self, obj):
        plan = HolidayPlan.objects.for_date(obj, date.today())
        if plan:
            return plan.allowance
        else:
            return None

    def fte(self, obj):
        plan = HolidayPlan.objects.for_date(obj, date.today())
        if plan:
            return plan.week_sum
        else:
            return None

    def allowance(self, obj):
        summary = _get_summary(obj)
        return summary["allowance"]

    def rollover(self, obj):
        summary = _get_summary(obj)
        return summary["rollover"]

    def public_holiday_adjustment(self, obj):
        summary = _get_summary(obj)
        return summary["public_holiday_adjustment"]

    public_holiday_adjustment.short_description = "B HOL ADJ"

    def total_allowance(self, obj):
        summary = _get_summary(obj)
        return f"{summary['total_allowance']:04.1f}"

    def total_used(self, obj):
        summary = _get_summary(obj)
        return f"{summary['total_used']:04.1f}"

    def remainder(self, obj):
        summary = _get_summary(obj)
        return ceil(summary["remainder"] * 2) / 2

    def allowance_minus_rollover(self, obj):
        summary = _get_summary(obj)
        return f"{summary['allowance_minus_rollover']:04.1f}"

    def jan_to_aug(self, obj):
        summary = _get_summary(obj)
        return f"{summary['jan_to_aug']:2.1f}"

    def jan_to_aug_frac(self, obj):
        summary = _get_summary(obj)
        return f"{summary['jan_to_aug_frac']*100:2.0f}%"

    def sep_to_nov(self, obj):
        summary = _get_summary(obj)
        return f"{summary['sep_to_nov']:2.1f}"

    change_form_template = "admin/holiday/change_form_holidayuser.html"

    def get_activity_summary(self, object_id):
        holiday_user = HolidayUser.objects.get(pk=object_id)
        plans = list(holiday_user.holiday_plans.order_by("start_date"))
        if len(plans) == 0:
            return []
        start_year = plans[0].start_date.year
        end_year = (
            date.today().year if plans[-1].allowance > 0 else plans[-1].start_date.year
        )
        summaries = []
        for year in range(start_year, end_year + 1):
            summary = generate_holiday_report(holiday_user.user, year)
            summaries.append(dict(summary=summary))

        return summaries[::-1]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if object_id is not None:
            extra_context = extra_context or {}
            extra_context["activity_list"] = self.get_activity_summary(object_id)
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )


@admin.register(HolidayPlan)
class HolidayPlanAdmin(admin.ModelAdmin):
    list_display = (
        "get_user",
        "start_date",
        "allowance",
        "mon_days",
        "tue_days",
        "wed_days",
        "thu_days",
        "fri_days",
        "sat_days",
        "sun_days",
    )
    search_fields = ("user__user__username",)

    def get_user(self, obj):
        return obj.user.user.username


@admin.register(HolidayRecord)
class HolidayRecordAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "start_date",
        "end_date",
        "adjustment",
        "record_type",
        "approved_by",
        "year",
    )
    search_fields = ("user__user__username",)
    list_filter = ("record_type",)


@admin.register(HolidayRecordType)
class HolidayRecordTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "system_option")


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ("user", "confirmed", "year")
    search_fields = ("user__user__username",)
