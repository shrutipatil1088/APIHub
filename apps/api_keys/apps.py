from django.apps import AppConfig


class ApiKeysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_keys"

    def ready(self):
        import apps.api_keys.signals  # noqa
