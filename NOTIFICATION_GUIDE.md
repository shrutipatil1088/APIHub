# APIHub - Real-Time Notification System Documentation

This document serves as the official reference guide for the **Real-Time Notification System** implemented in APIHub using Django Channels, Redis Channel Layer, Django REST Framework, and signal triggers.

---

## 1. Overview & Architecture

The notification system runs on **Django Channels** and operates independently of the dashboard analytics system.

- **WebSocket Route**: `ws://127.0.0.1:8000/ws/notifications/?token=<JWT_ACCESS_TOKEN>`
- **Authentication**: JWT token authentication via URL query parameter (`?token=...`).
- **Channel Groups**:
  - `notifications_admin`: Connected Admin users.
  - `notifications_user_<user_id>`: Connected Developer users (e.g. `notifications_user_7`).
- **Event Name**: `notification_created`

---

## 2. Notification Matrix (The 6 Events)

| # | Trigger Event | Trigger Endpoint / Action | Admin Recipient (`notifications_admin`) | Developer Recipient (`notifications_user_<user_id>`) | Notification Type |
|---|---|---|---|---|---|
| **1** | **Developer Registered** | `POST /api/v1/auth/register/` | ✅ Yes | ❌ No | `DEVELOPER_REGISTERED` |
| **2** | **Subscription Plan Created** | `POST /api/v1/subscription-plans/` | ✅ Yes | ❌ No | `SYSTEM` |
| **3** | **API Published** | `POST /api/v1/apis/` (with status `PUBLISHED`) | ✅ Yes | ❌ No | `API_PUBLISHED` |
| **4** | **Project Created** | `POST /api/v1/projects/` | ✅ Yes | ✅ Yes (Creator) | `PROJECT_CREATED` |
| **5** | **Subscription Activated** | `POST /api/v1/subscriptions/` | ✅ Yes | ✅ Yes (Subscriber) | `SUBSCRIPTION_CREATED` |
| **6** | **API Key Generated** | `POST /api/v1/api-keys/` | ✅ Yes | ✅ Yes (Project Owner) | `API_KEY_CREATED` |

---

## 3. Event Details & Payload Examples

### 1. Developer Registered
- **Action**: A new developer signs up.
- **Admin Message**: `"New Developer Registered: John Smith joined APIHub."`
- **Recipient**: Admin (`notifications_admin`)

### 2. Subscription Plan Created
- **Action**: Admin creates a new pricing plan template.
- **Admin Message**: `"New subscription plan 'Pro Plan' has been created."`
- **Recipient**: Admin (`notifications_admin`)

### 3. API Published
- **Action**: An API is created or updated to `PUBLISHED`.
- **Admin Message**: `"Payments API v2 has been published."`
- **Recipient**: Admin (`notifications_admin`)

### 4. Project Created
- **Action**: Developer creates a project.
- **Admin Message**: `"Project 'CRM App' was created by dev@example.com."`
- **Developer Message**: `"Project 'CRM App' was created successfully."`
- **Recipients**: Admin (`notifications_admin`) AND Developer (`notifications_user_<dev_id>`)

### 5. Subscription Activated
- **Action**: Developer subscribes to a plan.
- **Admin Message**: `"Developer dev@example.com activated Pro Plan subscription."`
- **Developer Message**: `"Your Pro Plan subscription is now active."`
- **Recipients**: Admin (`notifications_admin`) AND Developer (`notifications_user_<dev_id>`)

### 6. API Key Generated
- **Action**: Developer generates an API key for a project.
- **Admin Message**: `"A new API Key 'Key 1' was generated for project 'CRM App'."`
- **Developer Message**: `"A new API Key 'Key 1' has been generated."`
- **Recipients**: Admin (`notifications_admin`) AND Developer (`notifications_user_<dev_id>`)

---

## 4. WebSocket Payload Format

Every notification delivered over WebSocket uses this uniform JSON format:

```json
{
    "event": "notification_created",
    "notification": {
        "id": "aaf28683-bb4f-498f-a04e-6cf3f14343cf",
        "recipient_email": "developer@example.com",
        "title": "Project Created",
        "message": "Project 'CRM Integration' was created successfully.",
        "notification_type": "PROJECT_CREATED",
        "metadata": {
            "project_uuid": "351cb33d-dda4-4d2d-9f79-3f2f0477f8c6",
            "project_name": "CRM Integration"
        },
        "is_read": false,
        "created_at": "2026-07-31T10:56:35.776644Z"
    }
}
```

---

## 5. Notification REST APIs

The following REST API endpoints manage notification history in the database:

| Method | Endpoint | Description | Permissions |
|---|---|---|---|
| `GET` | `/api/v1/notifications/` | List latest notifications (ordered by `-created_at`, paginated) | Authenticated |
| `GET` | `/api/v1/notifications/unread-count/` | Get total unread count (`{"unread_count": N}`) | Authenticated |
| `PATCH` | `/api/v1/notifications/<uuid>/read/` | Mark a single notification as read | Owner / Admin |
| `POST` | `/api/v1/notifications/read-all/` | Mark all unread notifications as read | Authenticated |
| `DELETE` | `/api/v1/notifications/<uuid>/` | Soft-delete a notification | Owner / Admin |

---

## 6. How to Test (Step-by-Step)

1. Obtain a **JWT Access Token** from `POST /api/v1/auth/login/`.
2. Connect Postman WebSocket to:
   `ws://127.0.0.1:8000/ws/notifications/?token=<JWT_ACCESS_TOKEN>`
3. Execute any of the 6 trigger endpoints in Swagger UI or Postman HTTP.
4. Watch the `notification_created` JSON stream into your WebSocket window instantly!
