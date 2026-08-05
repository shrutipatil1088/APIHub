# APIHub Docker Setup & Operations Guide

Welcome to the **APIHub** Docker setup guide. This document provides a complete step-by-step walk-through for setting up, running, managing, and troubleshooting the APIHub Django application using Docker and Docker Compose on Windows.

---

## 1. Introduction

### Why Docker for APIHub?
Modern Django applications rely on complex ecosystems of background workers, asynchronous event loops, caching engines, and relational databases. Installing and configuring PostgreSQL, Redis, Celery, and Daphne separately on local machines often leads to environmental inconsistencies ("works on my machine" issues) and tedious manual setup.

Docker containerizes APIHub and all its backing services into isolated, predictable environments that behave identically across all developer machines and OS platforms.

### Architecture Overview & Services Used
The APIHub stack consists of five interconnected containers orchestrated via Docker Compose:

- **Django + Daphne (`web`)**: The core application server running Daphne (ASGI) to handle standard HTTP API requests as well as real-time WebSocket connections on port `8000`.
- **PostgreSQL (`db`)**: The relational database management system storing persistent application data (PostgreSQL 17).
- **Redis (`redis`)**: In-memory data storage used as a Celery task broker, result backend, and Django Channel Layer for real-time WebSockets.
- **Celery Worker (`celery_worker`)**: Asynchronous task worker processing background jobs (e.g., sending email notifications, asynchronous processing).
- **Celery Beat (`celery_beat`)**: Task scheduler enforcing periodic/cron tasks dispatched to the Celery worker queue.

---

## 2. Docker Desktop Installation (Windows)

### Step-by-Step Installation

1. **Download Docker Desktop**:
   Visit the official download page: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

2. **Select Architecture**:
   - Download the installer for **Windows AMD64** (for standard 64-bit x64 Intel/AMD processors).

3. **Install Docker Desktop**:
   - Run the executable installer (`Docker Desktop Installer.exe`).
   - On the Configuration screen, ensure **Use WSL 2 instead of Hyper-V (recommended)** is checked.
   - Follow the wizard and complete the installation.

4. **Enable WSL 2 Integration**:
   - Open Docker Desktop settings (`Settings` > `Resources` > `WSL Integration`).
   - Enable integration with your default WSL 2 distribution if prompted.

5. **System Restart**:
   - Restart your computer if required by the installer to finalize system features.

6. **Start Docker Desktop**:
   - Launch **Docker Desktop** from your Start Menu. Wait until the whale icon status in the system tray shows **Docker Desktop is running**.

### System Requirements
- **Hardware Virtualization**: Virtualization (Intel VT-x / AMD-V) must be enabled in your BIOS/UEFI settings.
- **WSL 2 (Windows Subsystem for Linux 2)**: Enabled in Windows Features (`Virtual Machine Platform` and `Windows Subsystem for Linux`).

### Verification Commands

Open PowerShell or Command Prompt and run the following commands to verify your setup:

```bash
docker --version
```
**Expected Output:**
```text
Docker version 27.0.3, build 6dca21e
``` *(Version numbers may vary)*

```bash
docker compose version
```
**Expected Output:**
```text
Docker Compose version v2.28.1
``` *(Version numbers may vary)*

```bash
docker ps
```
**Expected Output:**
```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```
*(If no containers are currently running, a clean table with header columns will be displayed without errors.)*

---

## 3. First Time Project Setup

### Navigate to Project Directory
Open your terminal (PowerShell or Bash) and change into the project root directory:

```bash
cd APIHub
```

### Key Configuration Files Overview
Before building, verify that the following essential Docker files are present in the project root:

- **`Dockerfile`**: Defines how the Python environment is constructed, system dependencies (`libpq-dev`, `netcat-openbsd`), Python packages, and the `entrypoint.sh` boot script.
- **`docker-compose.yml`**: Defines and configures all 5 services (`db`, `redis`, `web`, `celery_worker`, `celery_beat`), port mappings, network dependencies, healthchecks, and shared volumes.
- **`.env.docker`**: Contains environment variables passed into the containers (database credentials, hostnames `DB_HOST=db`, `REDIS_HOST=redis`, secret keys).
- **`entrypoint.sh`**: Startup script that waits for PostgreSQL and Redis health checks, runs migrations on the web container (`RUN_MIGRATIONS=true`), collects static files, and executes the primary service command.

Docker Compose automatically reads `docker-compose.yml` and feeds `.env.docker` variables into the containers during execution.

---

## 4. Build Docker Images

To construct the local Docker images defined in `docker-compose.yml`, run:

```bash
docker compose build
```

### What Happens During Build?
- Builds the APIHub web image from the `Dockerfile`.
- Pulls required base images from Docker Hub (`postgres:17-alpine`, `redis:7-alpine`).
- Installs all Python dependencies from `requirements.txt`.
- **Note**: This command builds/compiles images but does **not** start any containers.

---

## 5. Start Application

You can start the entire stack in one of two modes:

### Development Mode with Live Logs (Foreground)
```bash
docker compose up
```
- Starts all containers and streams real-time combined logs directly into your terminal window.
- Useful when debugging startup issues. Press `Ctrl + C` to stop the containers.

### Background / Detached Mode (Recommended for Daily Work)
```bash
docker compose up -d
```
- Starts all containers in the background (**detached mode**).
- Your terminal remains free for executing other local commands.

### Services Started
Running `docker compose up` starts the following services:
1. `web`
2. `db`
3. `redis`
4. `celery_worker`
5. `celery_beat`

---

## 6. Verify Running Containers

To check the current state and health of all project containers:

```bash
docker compose ps
```

### Expected Output & Status
```text
NAME                     IMAGE                  COMMAND                  SERVICE         CREATED         STATUS                   PORTS
apihub-db-1              postgres:17-alpine     "docker-entrypoint.s…"   db              10 minutes ago  Up 10 minutes (healthy)  0.0.0.0:5432->5432/tcp
apihub-redis-1           redis:7-alpine         "docker-entrypoint.s…"   redis           10 minutes ago  Up 10 minutes (healthy)  0.0.0.0:6379->6379/tcp
apihub-web-1             apihub-web             "/app/entrypoint.sh …"   web             10 minutes ago  Up 10 minutes            0.0.0.0:8000->8000/tcp
apihub-celery_worker-1   apihub-celery_worker   "/app/entrypoint.sh …"   celery_worker   10 minutes ago  Up 10 minutes            
apihub-celery_beat-1     apihub-celery_beat     "/app/entrypoint.sh …"   celery_beat     10 minutes ago  Up 10 minutes            
```

**Expected Service Statuses**:
- `web` → **Up**
- `db` → **Up (healthy)**
- `redis` → **Up (healthy)**
- `celery_worker` → **Up**
- `celery_beat` → **Up**

---

## 7. View Logs

### View Logs for All Services
To stream real-time logs from every container simultaneously:
```bash
docker compose logs -f
```
*(Press `Ctrl + C` to exit log viewing without stopping containers).*

### View Logs for Specific Services
To view logs for individual services:

**Django Web Server Logs:**
```bash
docker compose logs -f web
```

**Celery Worker Logs:**
```bash
docker compose logs -f celery_worker
```

**Celery Beat Logs:**
```bash
docker compose logs -f celery_beat
```

---

## 8. Stop Docker Application

### Stop Containers (Standard Removal)
```bash
docker compose down
```
- Stops and removes containers, networks, and default constructs created by Docker Compose.

### Difference Between `stop` and `down`

- `docker compose stop`:
  Stops running containers without removing them or destroying the Docker network.
- `docker compose down`:
  Stops containers and removes the containers and network entirely.

### Volume Preservation & Caution
Named volumes (`postgres_data`, `redis_data`, `static_volume`, `media_volume`) are preserved by default when using `docker compose down`.

To stop containers and remove volumes, run:
```bash
docker compose down -v
```

> [!CAUTION]
> Using `-v` (or `--volumes`) will **permanently delete named database volumes**, wiping out all PostgreSQL data, Redis cached data, and uploaded media! Use only when you want a completely fresh database start.

---

## 9. Restart Application

To restart running containers:

**Using Restart Command:**
```bash
docker compose restart
```

**Using Down and Up Cycle:**
```bash
docker compose down
docker compose up -d
```

---

## 10. Rebuild After Code or Dependency Changes

When modifying configuration files, dependencies, or the Dockerfile, the containers need to be rebuilt.

### Rebuild & Start Commands

**Foreground Mode:**
```bash
docker compose up --build
```

**Background (Detached Mode):**
```bash
docker compose up -d --build
```

### When to Rebuild
- Changes to `Dockerfile` or `entrypoint.sh`.
- Updates to `requirements.txt` or Python package dependencies.
- Changes to environment variables or build configurations.

---

## 11. Execute Commands Inside Container

You can execute commands directly inside the running `web` container.

### Interactive Bash Shell Access
```bash
docker compose exec web bash
```

### Direct Command Examples

**Run Database Migrations:**
```bash
docker compose exec web python manage.py migrate
```

**Create Superuser:**
```bash
docker compose exec web python manage.py createsuperuser
```

**Open Django Shell:**
```bash
docker compose exec web python manage.py shell
```

---

## 12. Database and Redis Information

Containers in the Docker Compose network communicate using **service names** as hostnames.

### Django Connection Settings
- **Database Connection**: `DB_HOST=db` (PostgreSQL service name)
- **Redis Connection**: `REDIS_HOST=redis` (Redis service name)

### Container Ports & Hosts
| Service | Internal Container Host | Port | Access URL |
| :--- | :--- | :--- | :--- |
| **Django (Daphne)** | `web` | `8000` | `http://localhost:8000` |
| **PostgreSQL** | `db` | `5432` | `localhost:5432` |
| **Redis** | `redis` | `6379` | `localhost:6379` |

---

## 13. Common Issues and Solutions

### A) Virtualization Support Not Detected
**Symptom**: Docker Desktop alerts that Hardware Virtualization is disabled or WSL 2 is missing.

**Solution**:
1. Reboot into BIOS/UEFI settings and enable **Virtualization Technology (VT-x / AMD-V)**.
2. Ensure **Virtual Machine Platform** and **Windows Subsystem for Linux** are enabled in Windows Features.
3. Install or update WSL 2 by running `wsl --update` in PowerShell.

### B) Port Already in Use (5432, 6379, 8000)
**Symptom**: Error when running `docker compose up`: `Bind for 0.0.0.0:5432 failed: port is already allocated`.

**Solution**:
A local service (e.g. local PostgreSQL server, local Redis, or local Django `manage.py runserver`) is running on your host machine.
- Identify the process using the port in PowerShell:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 5432).OwningProcess
  ```
- Stop local services via `services.msc` or terminate conflicting process before starting Docker.

### C) Migration Conflicts & Parallel Execution
**Symptom**: Database locks or race conditions during migrations when starting multiple container instances.

**Solution**:
APIHub uses the `RUN_MIGRATIONS` environment variable in `docker-compose.yml` to ensure only the `web` container executes migrations on startup:
- `web`: `RUN_MIGRATIONS=true`
- `celery_worker`: `RUN_MIGRATIONS=false`
- `celery_beat`: `RUN_MIGRATIONS=false`

---

## 14. Complete Daily Workflow

Use this quick summary for daily work:

1. **Start Laptop / Application**:
   ```bash
   docker compose up -d
   ```

2. **Check Container Status**:
   ```bash
   docker compose ps
   ```

3. **Develop Code**:
   Edit source code files directly in your IDE.

4. **Check Logs**:
   ```bash
   docker compose logs -f web
   ```

5. **Stop Application**:
   ```bash
   docker compose down
   ```

---

## 15. Production Notes

Note that Docker Compose configuration in this repository is designed for local development. For production deployment:

- **Nginx Reverse Proxy**: Place Nginx in front of Daphne to handle static/media files, SSL termination, and client buffering.
- **ASGI/WSGI Application Server**: Production Daphne/Gunicorn managed via process managers or container clusters.
- **CI/CD Integration**: Execute migrations in automated deployment pipelines as isolated single-run tasks before rolling out web containers.
- **Secrets Management**: Pass sensitive production keys via secure environment secret stores instead of `.env` files.
- **Managed Infrastructure**: Use managed cloud services (such as AWS RDS for PostgreSQL and ElastiCache for Redis) for high availability and automated backups.
