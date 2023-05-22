# Generated by Django 4.2.1 on 2023-05-22 15:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HolidayPlan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_date", models.DateField()),
                (
                    "allowance",
                    models.DecimalField(
                        blank=True, decimal_places=1, max_digits=4, null=True
                    ),
                ),
                (
                    "mon_days",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                (
                    "tue_days",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                (
                    "wed_days",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                (
                    "thu_days",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                (
                    "fri_days",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                (
                    "sat_days",
                    models.DecimalField(decimal_places=2, default=0, max_digits=3),
                ),
                (
                    "sun_days",
                    models.DecimalField(decimal_places=2, default=0, max_digits=3),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_modified", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="HolidayRecordType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100, unique=True)),
                ("code", models.CharField(max_length=5, unique=True)),
                ("system_option", models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name="HolidayUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="holidays",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HolidayRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("start_half", models.BooleanField(default=False)),
                ("end_half", models.BooleanField(default=False)),
                (
                    "adjustment",
                    models.DecimalField(
                        blank=True, decimal_places=1, max_digits=4, null=True
                    ),
                ),
                ("title", models.CharField(default="Annual Leave", max_length=255)),
                (
                    "approved_by",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("comment", models.CharField(blank=True, max_length=255, null=True)),
                ("year", models.IntegerField()),
                ("upstream_id", models.IntegerField(blank=True, null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_modified", models.DateTimeField(auto_now=True)),
                (
                    "holiday_plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="records",
                        to="teamsite_annual_leave.holidayplan",
                    ),
                ),
                (
                    "record_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="teamsite_annual_leave.holidayrecordtype",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="records",
                        to="teamsite_annual_leave.holidayuser",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="holidayplan",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="holiday_plans",
                to="teamsite_annual_leave.holidayuser",
            ),
        ),
        migrations.CreateModel(
            name="Confirmation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("confirmed", models.DateTimeField(auto_now_add=True)),
                ("year", models.IntegerField()),
                ("data", models.TextField(null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="holiday_confirmations",
                        to="teamsite_annual_leave.holidayuser",
                    ),
                ),
            ],
            options={
                "get_latest_by": "confirmed",
            },
        ),
        migrations.AlterUniqueTogether(
            name="holidayplan",
            unique_together={("user", "start_date")},
        ),
    ]
