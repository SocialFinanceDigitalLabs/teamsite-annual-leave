from datetime import date

from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models.confirmation import Confirmation
from .models.holiday_record import HolidayRecord
from .models.holiday_user import HolidayUser
from .permissions import IsEditableHoliday
from .serializers.activity_serializers import ActivitySummarySerializer
from .serializers.confirmation_serializer import ConfirmationSerializer
from .serializers.holiday_record_serializer import HolidayRecordSerializer
from .util.holiday_report import generate_holiday_report


class HolidayRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows organisations to be viewed or edited.
    """

    permission_classes = [permissions.IsAuthenticated, IsEditableHoliday]
    serializer_class = HolidayRecordSerializer

    def get_queryset(self):
        return HolidayRecord.objects.filter(user__user=self.request.user).order_by(
            "start_date"
        )

    def perform_create(self, serializer):
        start_date = serializer.validated_data.get("start_date")
        if start_date < date.today():
            raise serializers.ValidationError("Leave cannot be in the past")
        holiday_user = HolidayUser.objects.get(user=self.request.user)
        serializer.save(user=holiday_user, record_type_id=5)

    def perform_update(self, serializer):
        id = serializer.initial_data["id"]

        start_date = serializer.validated_data.get("start_date", date.today())

        original = HolidayRecord.objects.get(id=id)
        start_date = min(start_date, original.start_date)

        if start_date < date.today():
            raise serializers.ValidationError("Leave cannot be in the past")

        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if instance.start_date < date.today():
            raise serializers.ValidationError("Leave cannot be in the past")
        super().perform_destroy(instance)

    @action(detail=False)
    def activity(self, request):
        """
        Calculates the holiday summary for the current year, or optionally another year

        :param request:
        :return:
        """
        year = request.query_params.get("year", date.today().year)

        summary = generate_holiday_report(request.user, year)

        serializer = ActivitySummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=False)
    def public(self, request):
        year = request.query_params.get("year", date.today().year)
        qs = HolidayRecord.objects.filter(user__isnull=True, year=year).order_by(
            "start_date"
        )
        return Response(HolidayRecordSerializer(qs, many=True).data)


class ConfirmationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConfirmationSerializer

    def get_queryset(self):
        return Confirmation.objects.filter(user=self.request.user).order_by(
            "-confirmed"
        )

    def perform_create(self, serializer):
        holiday_user = HolidayUser.objects.get(user=self.request.user)
        serializer.save(user=holiday_user)
