from django.urls import include, path, re_path
from rest_framework import routers

from .views import ConfirmationViewSet, HolidayRecordViewSet

router = routers.DefaultRouter()
router.register(r"me", HolidayRecordViewSet, basename="holiday")
router.register(r"confirmation", ConfirmationViewSet, basename="holiday/confirmation")

urlpatterns = [
    path("", include(router.urls)),
]
