import importlib

from django.apps import AppConfig


class RmmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rmm"

    def ready(self):
        importlib.import_module("rmm.signals")
