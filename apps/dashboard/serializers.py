from rest_framework import serializers


class AdminDashboardSerializer(serializers.Serializer):
    """
    Serializer for Admin Dashboard analytics data.
    """

    total_apis = serializers.IntegerField()
    total_api_versions = serializers.IntegerField()
    total_endpoints = serializers.IntegerField()
    total_developers = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    total_api_keys = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    today_requests = serializers.IntegerField()
    this_month_requests = serializers.IntegerField()


class CurrentSubscriptionSerializer(serializers.Serializer):
    """
    Serializer for a developer's current active subscription details in Developer Dashboard.
    """

    uuid = serializers.UUIDField()
    plan = serializers.CharField()
    status = serializers.CharField()
    expires_at = serializers.DateTimeField()


class DeveloperDashboardSerializer(serializers.Serializer):
    """
    Serializer for Developer Dashboard analytics data.
    """

    my_projects = serializers.IntegerField()
    my_api_keys = serializers.IntegerField()
    my_requests_today = serializers.IntegerField()
    my_requests_this_month = serializers.IntegerField()
    current_subscription = CurrentSubscriptionSerializer(allow_null=True)
    remaining_requests = serializers.IntegerField(allow_null=True)
