from django.apps import AppConfig


class DeveloperProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.developer_projects"

    def ready(self):
        import apps.developer_projects.signals  # noqa
