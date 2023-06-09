from datetime import date

from rest_framework import permissions

from ..models.holiday_record import HolidayRecord


class IsEditableHoliday(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed for non system options
        return ~obj.record_type.system_option
