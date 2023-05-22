from rest_framework import serializers

from ..models.confirmation import Confirmation


class ConfirmationSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.ReadOnlyField(source="user.id")
    year = serializers.IntegerField()
    confirmed = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Confirmation
        fields = (
            "id",
            "user",
            "year",
            "confirmed",
        )
