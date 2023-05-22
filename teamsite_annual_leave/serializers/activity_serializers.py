from rest_framework import serializers


class ActivityDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    public_holiday_name = serializers.CharField()
    days_requested = serializers.FloatField()
    working_hours = serializers.FloatField()
    public_holiday = serializers.FloatField()
    allowance_used = serializers.FloatField()

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        if repr["public_holiday_name"] is None:
            del repr["public_holiday_name"]
        if repr["public_holiday"] is None:
            del repr["public_holiday"]
        return repr


class ActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.DateField()
    end = serializers.DateField()
    title = serializers.CharField()
    allowance_used = serializers.FloatField()
    adjustment = serializers.FloatField()
    total_allowance = serializers.FloatField()
    total_used = serializers.FloatField()
    remainder = serializers.FloatField()
    days = ActivityDaySerializer(many=True, required=False)

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        if repr["adjustment"] is None:
            del repr["adjustment"]
        if repr["allowance_used"] == 0:
            del repr["allowance_used"]
        return repr


class ActivitySummarySerializer(serializers.Serializer):
    year = serializers.IntegerField()
    total_allowance = serializers.FloatField()
    public_holiday_adjustment = serializers.FloatField()
    total_used = serializers.FloatField()
    remainder = serializers.FloatField()
    jan_to_aug = serializers.FloatField()
    jan_to_aug_frac = serializers.FloatField()
    sep_to_nov = serializers.FloatField()
    allowance_minus_rollover = serializers.FloatField()
    last_confirmed = serializers.DateTimeField(allow_null=True)
    details = ActivitySerializer(many=True, required=False)
