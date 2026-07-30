from django.apps import AppConfig


class UsageLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usage_logs'

    # Runs once when Django finishes loading the app.
    # Runs once on app startup to register all signal handlers.
    def ready(self):
        """
        Registers UsageLog signals on app startup.
        """
        import apps.usage_logs.signals  # noqa: F401
