from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.models import User
from apps.core.pagination import StandardResultsSetPagination
from apps.core.responses import success_response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """
    GET /api/v1/notifications/
    Returns paginated list of notifications ordered by -created_at.
    - Developer users: View notifications assigned to them (recipient=user).
    - Admin users: View admin notifications (recipient=None or recipient=user).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
        summary="List Notifications",
        description="Returns a paginated list of notifications for the authenticated user.",
        responses={200: NotificationSerializer(many=True)},
    )
    def get(self, request):
        user = request.user
        if user.role == User.Role.ADMIN:
            queryset = Notification.objects.filter(
                Q(recipient__isnull=True) | Q(recipient=user),
                is_deleted=False,
            )
        else:
            queryset = Notification.objects.filter(
                recipient=user,
                is_deleted=False,
            )

        queryset = queryset.order_by("-created_at")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class NotificationMarkReadView(APIView):
    """
    PATCH /api/v1/notifications/<uuid>/read/
    Marks a single notification as read.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
        summary="Mark Notification as Read",
        description="Marks a single notification as read.",
        responses={200: NotificationSerializer},
    )
    def patch(self, request, uuid):
        user = request.user
        notification = get_object_or_404(Notification, uuid=uuid, is_deleted=False)

        # Check permissions
        if user.role == User.Role.DEVELOPER and notification.recipient != user:
            raise PermissionDenied("You do not have permission to modify this notification.")

        if user.role == User.Role.ADMIN and notification.recipient is not None and notification.recipient != user:
            raise PermissionDenied("You do not have permission to modify this notification.")

        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])

        serializer = NotificationSerializer(notification)
        return success_response(
            data=serializer.data,
            message="Notification marked as read.",
            status_code=status.HTTP_200_OK,
        )


class NotificationMarkAllReadView(APIView):
    """
    POST /api/v1/notifications/read-all/
    Marks all notifications for the authenticated user/role as read.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
        summary="Mark All Notifications as Read",
        description="Marks all unread notifications for the authenticated user as read.",
        responses={200: OpenApiResponse(description="All notifications marked as read.")},
    )
    def post(self, request):
        user = request.user
        if user.role == User.Role.ADMIN:
            queryset = Notification.objects.filter(
                Q(recipient__isnull=True) | Q(recipient=user),
                is_read=False,
                is_deleted=False,
            )
        else:
            queryset = Notification.objects.filter(
                recipient=user,
                is_read=False,
                is_deleted=False,
            )

        updated_count = queryset.update(
            is_read=True,
            updated_at=timezone.now(),
        )

        return success_response(
            data={"marked_read_count": updated_count},
            message=f"Marked {updated_count} notification(s) as read.",
            status_code=status.HTTP_200_OK,
        )


class NotificationUnreadCountView(APIView):
    """
    GET /api/v1/notifications/unread-count/
    Returns the total unread notifications count for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Unread Notification Count",
        description="Returns total unread notification count.",
        responses={200: OpenApiResponse(description="Unread notification count.")},
    )
    def get(self, request):
        user = request.user
        if user.role == User.Role.ADMIN:
            unread_count = Notification.objects.filter(
                Q(recipient__isnull=True) | Q(recipient=user),
                is_read=False,
                is_deleted=False,
            ).count()
        else:
            unread_count = Notification.objects.filter(
                recipient=user,
                is_read=False,
                is_deleted=False,
            ).count()

        return success_response(
            data={"unread_count": unread_count},
            message="Unread notification count retrieved.",
            status_code=status.HTTP_200_OK,
        )


class NotificationDetailDeleteView(APIView):
    """
    DELETE /api/v1/notifications/<uuid>/
    Soft deletes a notification.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
        summary="Soft Delete Notification",
        description="Soft-deletes a single notification.",
        responses={200: OpenApiResponse(description="Notification soft deleted.")},
    )
    def delete(self, request, uuid):
        user = request.user
        notification = get_object_or_404(Notification, uuid=uuid, is_deleted=False)

        # Check permissions
        if user.role == User.Role.DEVELOPER and notification.recipient != user:
            raise PermissionDenied("You do not have permission to delete this notification.")

        if user.role == User.Role.ADMIN and notification.recipient is not None and notification.recipient != user:
            raise PermissionDenied("You do not have permission to delete this notification.")

        notification.soft_delete()

        return success_response(
            data=None,
            message="Notification deleted successfully.",
            status_code=status.HTTP_200_OK,
        )
