from django.utils import timezone

from apps.accounts.models import User
from apps.api_catalog.models import API, APIVersion, Endpoint
from apps.developer_projects.models import DeveloperProject
from apps.api_keys.models import APIKey
from apps.subscriptions.models import UserSubscription
from apps.usage_logs.models import UsageLog


class DashboardService:
    """
    Contains business logic and database aggregation queries for the Dashboard module.
    """

    @staticmethod
    def get_admin_dashboard(user):
        """
        Calculates and returns platform-wide analytics for Admin users.
        """
        now = timezone.now()
        today = now.date()

        total_apis = API.objects.filter(is_deleted=False).count()
        total_api_versions = APIVersion.objects.filter(is_deleted=False).count()
        total_endpoints = Endpoint.objects.filter(is_deleted=False).count()
        total_developers = User.objects.filter(
            role=User.Role.DEVELOPER,
            is_deleted=False,
        ).count()
        total_projects = DeveloperProject.objects.filter(is_deleted=False).count()
        total_api_keys = APIKey.objects.filter(is_deleted=False).count()
        active_subscriptions = UserSubscription.objects.filter(
            status=UserSubscription.Status.ACTIVE,
            is_deleted=False,
        ).count()
        today_requests = UsageLog.objects.filter(
            requested_at__date=today,
            is_deleted=False,
        ).count()
        this_month_requests = UsageLog.objects.filter(
            requested_at__year=now.year,
            requested_at__month=now.month,
            is_deleted=False,
        ).count()

        return {
            "total_apis": total_apis,
            "total_api_versions": total_api_versions,
            "total_endpoints": total_endpoints,
            "total_developers": total_developers,
            "total_projects": total_projects,
            "total_api_keys": total_api_keys,
            "active_subscriptions": active_subscriptions,
            "today_requests": today_requests,
            "this_month_requests": this_month_requests,
        }

    @staticmethod
    def get_developer_dashboard(user):
        """
        Calculates and returns developer-specific analytics for the authenticated developer user.
        """
        now = timezone.now()
        today = now.date()

        my_projects = DeveloperProject.objects.filter(
            developer=user,
            is_deleted=False,
        ).count()

        my_api_keys = APIKey.objects.filter(
            project__developer=user,
            is_deleted=False,
        ).count()

        my_requests_today = UsageLog.objects.filter(
            project__developer=user,
            requested_at__date=today,
            is_deleted=False,
        ).count()

        my_requests_this_month = UsageLog.objects.filter(
            project__developer=user,
            requested_at__year=now.year,
            requested_at__month=now.month,
            is_deleted=False,
        ).count()

        # Fetch current active subscription for the developer
        subscription = (
            UserSubscription.objects
            .select_related("plan")
            .filter(
                user=user,
                status=UserSubscription.Status.ACTIVE,
                is_deleted=False,
            )
            .order_by("-created_at")
            .first()
        )

        current_subscription_data = None
        remaining_requests = None

        if subscription:
            current_subscription_data = {
                "uuid": subscription.uuid,
                "plan": subscription.plan.name,
                "status": subscription.status,
                "expires_at": subscription.end_date,
            }

            plan = subscription.plan

            # Check if plan is Unlimited or Enterprise
            is_unlimited = (
                plan.request_limit == 0
                or "enterprise" in plan.name.lower()
                or "unlimited" in plan.name.lower()
            )

            if not is_unlimited:
                # Count requests made under the current active subscription since its start_date
                current_sub_requests = UsageLog.objects.filter(
                    api_key__subscription=subscription,
                    is_deleted=False,
                    requested_at__gte=subscription.start_date,
                ).count()
                remaining_requests = max(0, plan.request_limit - current_sub_requests)

        return {
            "my_projects": my_projects,
            "my_api_keys": my_api_keys,
            "my_requests_today": my_requests_today,
            "my_requests_this_month": my_requests_this_month,
            "current_subscription": current_subscription_data,
            "remaining_requests": remaining_requests,
        }
