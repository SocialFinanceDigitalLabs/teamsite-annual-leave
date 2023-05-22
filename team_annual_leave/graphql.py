from datetime import date

import django_filters
from django.db.models import Q
from graphene import Boolean, relay
from graphene_django.types import DjangoObjectType

from .models.holiday_record import HolidayRecord


class HolidayRecordNode(DjangoObjectType):
    today = Boolean()

    @staticmethod
    def resolve_today(record, info):
        today = date.today()
        return record.start_date <= today <= record.end_date

    class Meta:
        model = HolidayRecord
        filter_fields = {
            "start_date": ["exact", "gt", "gte", "lt", "lte"],
            "end_date": ["exact", "gt", "gte", "lt", "lte"],
        },
        interfaces = (relay.Node,)
        fields = [
            "title",
            "start_date",
            "end_date",
            "start_half",
            "end_half",
            "user",
            "today",
        ]


class HolidayRecordFilter(django_filters.FilterSet):
    upcoming = django_filters.BooleanFilter(method="filter_upcoming")

    @classmethod
    def filter_upcoming(cls, queryset, name, value):
        today = date.today()
        query = Q(end_date__gte=today)
        if value:
            return queryset.filter(query)
        else:
            return queryset.filter(~query)

