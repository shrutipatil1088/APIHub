from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
    NotificationDetailDeleteView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/unread-count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/read-all/", NotificationMarkAllReadView.as_view(), name="notification-read-all"),
    path("notifications/<uuid:uuid>/read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("notifications/<uuid:uuid>/", NotificationDetailDeleteView.as_view(), name="notification-detail-delete"),
]
