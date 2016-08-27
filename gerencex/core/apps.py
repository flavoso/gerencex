from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'gerencex.core'

    def ready(self):
        import gerencex.core.signals
