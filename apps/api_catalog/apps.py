from django.apps import AppConfig


class ApiCatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_catalog"

    def ready(self):
        import apps.api_catalog.signals  # noqa
