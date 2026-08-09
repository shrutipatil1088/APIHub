# 🚀 APIHub Production Deployment Guide

This guide documents the exact step-by-step production deployment architecture for **APIHub** using free cloud infrastructure.

---

## 🛠️ Deployment Architecture Overview

APIHub uses a decoupled cloud infrastructure to deliver high performance, 24/7 database persistence, and real-time WebSockets on a $0/month budget:

| Component | Cloud Platform | Free Plan | Purpose |
| :--- | :--- | :--- | :--- |
| **Django Web App** | [Render](https://render.com) | Free Web Service | Hosts Daphne ASGI server, executes REST APIs & WebSockets. |
| **PostgreSQL Database**| [Supabase](https://supabase.com) | Free Forever (500 MB) | Relational database storing accounts, APIs, keys, logs, & subscriptions. |
| **Redis Cache & Broker**| [Upstash](https://upstash.com) | Free Serverless (10k cmd/day) | In-memory store for Celery task queue & Channels WebSockets. |

---

## 📌 Step 1: Set Up PostgreSQL on Supabase

1. Go to **[supabase.com](https://supabase.com)** and sign in with your GitHub account.
2. Click **New Project** ➔ Name it `apihub-db`.
3. Set a strong **Database Password** and select region (e.g. `ap-south-1 (Mumbai)`).
4. Click **Create new project**.
5. Once created, go to **Project Settings** (`⚙️`) ➔ **Database** ➔ **Connection String** ➔ **URI**.
6. Copy the database connection host details:
   - `DB_HOST`: `aws-0-ap-south-1.pooler.supabase.com`
   - `DB_NAME`: `postgres`
   - `DB_USER`: `postgres.yunflafzcdwuccwcdumq`
   - `DB_PORT`: `6543` (or `5432`)

---

## ⚡ Step 2: Set Up Serverless Redis on Upstash

1. Go to **[upstash.com](https://upstash.com)** and sign in with your GitHub account.
2. Click **Create Database**.
3. Set **Name**: `apihub-redis`, **Type**: `Redis`, **Region**: `ap-south-1 (Mumbai)`.
4. Click **Create**.
5. Under connection details, copy the **Redis URL** (starts with `rediss://` for SSL):
   ```text
   rediss://default:<YOUR_UPSTASH_TOKEN>@handy-tomcat-169355.upstash.io:6379
   ```

---

## 🌐 Step 3: Deploy Django Application on Render

1. Go to **[dashboard.render.com](https://dashboard.render.com)** and log in with GitHub.
2. Click **New +** ➔ Select **Web Service**.
3. Connect your repository: **`shrutipatil1088/APIHub`**.
4. Configure settings:
   - **Name**: `apihub-backend`
   - **Language / Runtime**: `Docker`
   - **Branch**: `main`
   - **Instance Type**: `Free ($0/month)`
5. Click **Add from .env** and paste your production environment variables:

```text
SECRET_KEY=django-insecure-render-secret-key-12345
DEBUG=False
ALLOWED_HOSTS=.onrender.com
DB_HOST=aws-0-ap-south-1.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.yunflafzcdwuccwcdumq
DB_PASSWORD=<YOUR_SUPABASE_PASSWORD>
DB_PORT=6543
POSTGRES_HOST=aws-0-ap-south-1.pooler.supabase.com
POSTGRES_DB=postgres
POSTGRES_USER=postgres.yunflafzcdwuccwcdumq
POSTGRES_PASSWORD=<YOUR_SUPABASE_PASSWORD>
POSTGRES_PORT=6543
REDIS_URL=rediss://default:<YOUR_UPSTASH_TOKEN>@handy-tomcat-169355.upstash.io:6379
CELERY_BROKER_URL=rediss://default:<YOUR_UPSTASH_TOKEN>@handy-tomcat-169355.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://default:<YOUR_UPSTASH_TOKEN>@handy-tomcat-169355.upstash.io:6379
RUN_MIGRATIONS=true
```

6. Click **Deploy Web Service**. Render will build the container via `Dockerfile`, run database migrations via `entrypoint.sh`, and publish your service live!

---

## 🔑 Step 4: Promote Admin User

To promote a registered user to Superadmin:
1. Go to **Supabase Dashboard** ➔ **SQL Editor** ➔ **New Query**.
2. Run this query:
```sql
UPDATE accounts_user 
SET role = 'ADMIN', is_superuser = true, is_staff = true 
WHERE email = 'your_registered_email@example.com';
```

---

## 🌐 Live Production Endpoints

- **Live Backend Base URL**: [https://apihub-6k8m.onrender.com/](https://apihub-6k8m.onrender.com/)
- **Interactive Swagger Documentation**: [https://apihub-6k8m.onrender.com/api/docs/](https://apihub-6k8m.onrender.com/api/docs/)
- **Health Check Endpoint**: [https://apihub-6k8m.onrender.com/api/v1/health/](https://apihub-6k8m.onrender.com/api/v1/health/)
- **Live Admin Portal**: [https://apihub-6k8m.onrender.com/admin/](https://apihub-6k8m.onrender.com/admin/)
- **WebSocket Notifications**: `wss://apihub-6k8m.onrender.com/ws/notifications/?token=<JWT_TOKEN>`
- **WebSocket Dashboards**: `wss://apihub-6k8m.onrender.com/ws/dashboard/?token=<JWT_TOKEN>`
