from rest_framework import serializers

from ..models.holiday_record import HolidayRecord
from ..models.holiday_record_type import HolidayRecordType


class HolidayRecordSerializer(serializers.HyperlinkedModelSerializer):
    record_type = serializers.PrimaryKeyRelatedField(
        queryset=HolidayRecordType.objects.all().filter(system_option=False)
    )
    user = serializers.ReadOnlyField(source="user.id")
    start_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%d/%m/%Y", "iso-8601"]
    )
    end_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%d/%m/%Y", "iso-8601"]
    )

    class Meta:
        model = HolidayRecord
        fields = [
            "id",
            "start_date",
            "end_date",
            "start_half",
            "end_half",
            "adjustment",
            "record_type",
            "title",
            "approved_by",
            "user",
            "year",
        ]
