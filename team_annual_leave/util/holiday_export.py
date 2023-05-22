import calendar
from datetime import date, datetime, timedelta
from functools import reduce
from io import BytesIO
from math import ceil

import pytz
import xlsxwriter
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from ..models.holiday_plan import HolidayPlan, HolidayPlanCacheLookup
from ..models.holiday_record import HolidayRecord
from ..models.holiday_user import HolidayUser
from ..util.excel_column_counter import ColumnCounter
from ..util.holiday_report import _search_system_records, generate_holiday_report


def get_users(usernames=None):
    if usernames is not None:
        usernames = usernames.split(",")
        usernames = [u.strip() for u in usernames]
        usernames = reduce(
            lambda x, y: x | y, [Q(username__icontains=u) for u in usernames]
        )
        users = User.objects.filter(usernames)
    else:
        users = User.objects.all()

    return users.order_by("username")


def get_user_reports(users, year):
    reports = []
    for user in users:
        report = generate_holiday_report(user, year)
        if report is not None and len(report["details"]) > 0:
            reports.append((user, report))
    return reports


def add_summary_view(workbook, reports):
    summary_data = []

    for user, report in reports:
        last_confirmed = report.get("last_confirmed")
        if last_confirmed is not None:
            last_confirmed = last_confirmed.astimezone(
                pytz.timezone("Europe/London")
            ).replace(tzinfo=None)

        summary_data.append(
            [
                user.email,
                user.profile.short_name,
                report["year"],
                report["allowance"],
                report["rollover"],
                report["public_holiday_adjustment"],
                report["total_allowance"]
                - report["rollover"]
                - report["allowance"]
                - report["public_holiday_adjustment"],
                report["total_allowance"],
                report["total_used"],
                report["remainder"],
                report["allowance_minus_rollover"],
                report["jan_to_aug"],
                report["jan_to_aug_frac"],
                report["sep_to_nov"],
                last_confirmed,
            ]
        )

    summary_columns = [
        {"header": c}
        for c in [
            "Email",
            "Name",
            "Year",
            "Allowance",
            "Rollover",
            "Public Holiday Adjustments",
            "Other Adjustments",
            "Total Debits",
            "Total Credits",
            "Remaining",
            "Initial Allowance (-Rollover)",
            "January to August",
            "January to August Fraction",
            "September to November",
            "Last Confirmed",
        ]
    ]

    pct_format = workbook.add_format()
    pct_format.set_num_format("0%")

    warning_format = workbook.add_format()
    warning_format.set_num_format("0%")
    warning_format.set_bg_color("#ffa3a3")

    warning_format2 = workbook.add_format()
    warning_format2.set_bg_color("#ffa3a3")

    date_format = workbook.add_format()
    date_format.set_num_format("mmm d yyyy h:mm AM/PM")

    worksheet = workbook.add_worksheet(name="Summary")

    worksheet.add_table(
        0,
        0,
        len(summary_data),
        len(summary_columns) - 1,
        {"data": summary_data, "columns": summary_columns, "name": "HolidaysSummary"},
    )
    worksheet.set_column("A:A", 35)
    worksheet.set_column("B:I", 15)
    worksheet.set_column("J:L", 25)
    worksheet.set_column("M:M", 24, pct_format)
    worksheet.set_column("N:N", 17)
    worksheet.set_column("O:O", 24, date_format)

    worksheet.conditional_format(
        f"M2:M{len(summary_data)}",
        {"type": "cell", "criteria": "<", "value": 0.5, "format": warning_format},
    )

    worksheet.conditional_format(
        f"N2:N{len(summary_data)}",
        {"type": "cell", "criteria": ">", "value": 8, "format": warning_format2},
    )

    worksheet.freeze_panes(1, 2)


def add_detail_view(workbook, reports):
    detailed_data = []
    for user, report in reports:
        for record in report["details"]:
            detailed_data.append(
                [
                    user.email,
                    user.profile.short_name,
                    report["year"],
                    record["title"],
                    record["start"],
                    record["end"],
                    record["adjustment"],
                    record["allowance_used"],
                    record["total_used"],
                    ceil(record["remainder"] * 2) / 2,
                    record["remainder"],
                    record["approved_by"],
                ]
            )

    detailed_columns = [
        {"header": c}
        for c in [
            "Email",
            "Name",
            "Year",
            "Title",
            "Start Date",
            "End Date",
            "Adjustment",
            "Days Taken",
            "Days Taken (to date)",
            "Remaining Days",
            "Remaining Days (exact)",
            "Approved By",
        ]
    ]

    date_format = workbook.add_format()
    date_format.set_num_format("d mmm yyyy")

    worksheet = workbook.add_worksheet(name="Detailed Report")

    worksheet.add_table(
        0,
        0,
        len(detailed_data),
        len(detailed_columns) - 1,
        {
            "data": detailed_data,
            "columns": detailed_columns,
            "name": "HolidaysDetailed",
        },
    )

    cc = ColumnCounter()
    worksheet.set_column(cc.next(1), 35)
    worksheet.set_column(cc.next(1), 15)
    worksheet.set_column(cc.next(1), 8)
    worksheet.set_column(cc.next(1), 30)
    worksheet.set_column(cc.next(2), 11, date_format)
    worksheet.set_column(cc.next(5), 15)
    worksheet.set_column(cc.next(1), 35)

    worksheet.freeze_panes(1, 2)


def add_calendar(workbook, reports, year, upcoming=False, next_year=None):
    worksheet = workbook.add_worksheet(name="Calendar")
    if next_year is not None:
        next_year = {r[0]: r[1] for r in next_year}

    company_holidays = HolidayRecord.objects.filter(user__isnull=True)

    if upcoming:
        d_start = datetime.today()
        d_start = (d_start - timedelta(days=d_start.weekday())).date()
    else:
        d_start = date(year, 1, 1)

    if next_year is not None:
        days_in_year = (date(year + 1, 6, 30) - d_start).days + 1
    else:
        days_in_year = (date(year, 12, 31) - d_start).days + 1

    start_col = 2

    default_properties = dict(border=1, border_color="#cccccc")

    format_row_even = workbook.add_format(default_properties)

    format_row_odd = workbook.add_format(default_properties)
    format_row_odd.set_bg_color("#eeeeee")

    format_weekend = workbook.add_format(default_properties)
    format_weekend.set_bg_color("#d5e1df")

    format_bank_holiday = workbook.add_format(default_properties)
    format_bank_holiday.set_bg_color("#d5e1df")
    format_bank_holiday.set_fg_color("#ffffff")
    format_bank_holiday.set_pattern(15)

    format_holiday = workbook.add_format()
    format_holiday.set_bg_color("#eca1a6")

    format_holiday_half = workbook.add_format(default_properties)
    format_holiday_half.set_bg_color("#eca1a6")
    format_holiday_half.set_fg_color("#ffffff")
    format_holiday_half.set_pattern(15)

    format_non_working = workbook.add_format(default_properties)
    format_non_working.set_bg_color("#b5e7a0")

    format_non_working_half = workbook.add_format(default_properties)
    format_non_working_half.set_bg_color("#b5e7a0")
    format_non_working_half.set_fg_color("#ffffff")
    format_non_working_half.set_pattern(15)

    format_non_working_holiday = workbook.add_format(default_properties)
    format_non_working_holiday.set_bg_color("#eca1a6")
    format_non_working_holiday.set_fg_color("#b5e7a0")
    format_non_working_holiday.set_pattern(15)

    format_header_props = {
        "font_color": "#FFFFFF",
        "bold": True,
        "align": "center",
        "valign": "vcenter",
        "border_color": "#cccccc",
        "left": 1,
        "right": 1,
    }

    format_header_dark = workbook.add_format(format_header_props)
    format_header_dark.set_bg_color("#1E3F66")
    format_header_dark.set_top(0)

    format_header_light = workbook.add_format(format_header_props)
    format_header_light.set_bg_color("#2E5984")
    format_header_light.set_top(0)

    # Headers
    worksheet.merge_range(0, 0, 1, 0, "Email", format_header_dark)
    worksheet.merge_range(0, 1, 1, 1, "Name", format_header_dark)

    for ix in range(0, 13):
        m_start = date(year, d_start.month, 1) + relativedelta(months=ix)
        if (m_start - d_start).days >= days_in_year:
            break

        weekday, numdays = calendar.monthrange(m_start.year, m_start.month)

        day_start = (m_start - d_start).days
        day_end = day_start + numdays - 1

        if day_start < 0:
            day_start = 0

        format = format_header_light if m_start.month % 2 == 0 else format_header_dark
        worksheet.merge_range(
            0,
            start_col + day_start,
            0,
            start_col + day_end,
            m_start.strftime("%B"),
            format,
        )

    for day_of_year in range(0, days_in_year):
        d = d_start + timedelta(days=day_of_year)
        format = format_header_light if d.month % 2 == 0 else format_header_dark
        worksheet.write(1, start_col + day_of_year, d.day, format)

    # Users
    plan_lookup = HolidayPlanCacheLookup()
    start_row = 2
    empty_row = ["" for r in range(0, days_in_year)]
    for ix, (user, report) in enumerate(reports):
        user_row = start_row + ix

        holiday_user = HolidayUser.objects.get(user=user)

        format = format_row_odd if user_row % 2 == 0 else format_row_even

        worksheet.write(user_row, 0, user.email, format)
        worksheet.write(user_row, 1, user.profile.short_name, format)
        worksheet.write_row(user_row, 2, empty_row, format)

        for day_of_year in range(0, days_in_year):
            d = d_start + timedelta(days=day_of_year)
            plan = plan_lookup.get_for_user_and_date(holiday_user, d)
            if plan is None or plan.allowance == 0:
                worksheet.write(
                    user_row, start_col + day_of_year, "", format_non_working
                )
            else:
                working_days = plan.get_days_for_day_of_week(d.weekday())
                if working_days == 0:
                    worksheet.write(
                        user_row, start_col + day_of_year, "", format_non_working
                    )
                elif working_days < 1:
                    worksheet.write(
                        user_row, start_col + day_of_year, "", format_non_working_half
                    )

        records = report["details"]
        if next_year is not None:
            records += next_year.get(user, {}).get("details", [])
        for record in records:
            for d in record.get("days", []):
                allowance_used = d.get("allowance_used", 0)
                if allowance_used > 0:
                    day_of_year = (d["date"] - d_start).days
                    if allowance_used == 1:
                        worksheet.write(
                            user_row, start_col + day_of_year, "", format_holiday
                        )
                    elif d["working_hours"] < 1:
                        worksheet.write(
                            user_row,
                            start_col + day_of_year,
                            "",
                            format_non_working_holiday,
                        )
                    else:
                        worksheet.write(
                            user_row, start_col + day_of_year, "", format_holiday_half
                        )

    worksheet.set_column("A:A", 35)
    worksheet.set_column("B:B", 15)
    worksheet.set_column(start_col, start_col + days_in_year, 2.5)

    empty_column = ["" for r in reports]

    # Add weekends and bank holidays
    for day_of_year in range(0, days_in_year):
        d = d_start + timedelta(days=day_of_year)
        if d.weekday() >= 5:
            worksheet.write_column(
                start_row, start_col + day_of_year, empty_column, format_weekend
            )
            continue

        holiday = _search_system_records(company_holidays, d)
        if holiday is not None:
            worksheet.write_column(
                start_row, start_col + day_of_year, empty_column, format_bank_holiday
            )

    worksheet.freeze_panes(2, 2)


def add_plan_view(workbook):
    plan_result = HolidayPlan.objects.all().order_by(
        "user__user__username", "start_date"
    )
    plan_rows = []
    for plan in plan_result:
        plan_rows.append(
            [
                plan.user.user.email,
                plan.user.user.profile.short_name,
                plan.start_date,
                plan.end_date,
                plan.allowance,
                plan.week_sum / 5,
            ]
        )

    columns = [
        {"header": c}
        for c in [
            "Email",
            "Name",
            "Start",
            "End",
            "Allowance",
            "FTE",
        ]
    ]

    date_format = workbook.add_format()
    date_format.set_num_format("d mmm yyyy")

    fte_format = workbook.add_format()
    fte_format.set_num_format("0.00")

    worksheet = workbook.add_worksheet(name="Leave Plans")

    worksheet.add_table(
        0,
        0,
        len(plan_rows),
        len(columns) - 1,
        {"data": plan_rows, "columns": columns, "name": "LeavePlans"},
    )

    cc = ColumnCounter()
    worksheet.set_column(cc.next(1), 35)
    worksheet.set_column(cc.next(1), 15)
    worksheet.set_column(cc.next(2), 11, date_format)
    worksheet.set_column(cc.next(1), 11)
    worksheet.set_column(cc.next(1), 11, fte_format)

    worksheet.freeze_panes(1, 2)


def create_holiday_report(output, usernames, year, config="csd"):
    users = get_users(usernames)
    reports = get_user_reports(users, year)
    reports = [
        r for r in reports if r[1].get("allowance", 0) > 0
    ]  # Not the most optimal, should consider query filter

    workbook = xlsxwriter.Workbook(output)
    # workbook.set_readonly_recommended(True)

    for char in config:
        if char == "c":
            add_calendar(workbook, reports, year)
        elif char == "u":
            if timezone.now().month >= 6:
                next_year = get_user_reports(users, year + 1)
            else:
                next_year = None
            add_calendar(workbook, reports, year, upcoming=True, next_year=next_year)
        elif char == "s":
            add_summary_view(workbook, reports)
        elif char == "d":
            add_detail_view(workbook, reports)
        elif char == "p":
            add_plan_view(workbook)
        else:
            raise Exception(f"Unknown option string encountered: {config}")

    workbook.close()
