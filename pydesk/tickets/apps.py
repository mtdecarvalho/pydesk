from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TicketsConfig(AppConfig):
    name = "tickets"

    def ready(self):
        from .signals import criar_grupos_e_permissoes

        post_migrate.connect(
            criar_grupos_e_permissoes,
            sender=self,
            dispatch_uid="tickets.criar_grupos_e_permissoes",
        )
