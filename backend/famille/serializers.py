from rest_framework import serializers

from .models import ChildDevice, EnrollInvite, InstalledApp, Position


class DeviceSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = ChildDevice
        fields = ["id", "label", "phone", "platform", "sharing_on", "sharing_changed_at",
                  "last_lat", "last_lon", "last_battery", "last_seen_at", "status"]

    def get_status(self, obj):
        if not obj.sharing_on:
            return "paused"          # l'enfant a coupé — honnête, affiché tel quel
        if obj.last_seen_at is None:
            return "never"
        return "active"


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["lat", "lon", "battery", "recorded_at"]


class AppSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstalledApp
        fields = ["package", "name"]


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollInvite
        fields = ["id", "token", "child_label", "phone", "used_at", "created_at"]
        read_only_fields = ["token", "used_at", "created_at"]
