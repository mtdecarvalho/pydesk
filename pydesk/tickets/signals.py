from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def criar_grupos_e_permissoes(sender, **kwargs):
    # Importação tardia para evitar problemas na inicialização do registro de apps
    from .models import Historico, Ticket

    # Importa ou cria os grupos
    grupo_tecnico, _ = Group.objects.get_or_create(name="TECNICO")
    grupo_usuario_comum, _ = Group.objects.get_or_create(name="USUARIO_COMUM")

    # Obtém os ContentTypes de Ticket e Historico para filtrar permissões vinculadas exatamente a esses modelos
    ticket_ct = ContentType.objects.get_for_model(Ticket)
    historico_ct = ContentType.objects.get_for_model(Historico)

    # USUARIO_COMUM: permissões base + permissão de cancelar tkts
    permissoes_usuario_comum = Permission.objects.filter(
        content_type=ticket_ct,
        codename__in=["add_ticket", "view_ticket", "pode_cancelar"],
    )

    # TECNICO: permissões base + visualização de histórico + permissão de encerrar tkts
    permissoes_tecnico = Permission.objects.filter(
        content_type=ticket_ct,
        codename__in=["add_ticket", "change_ticket", "view_ticket", "pode_encerrar"],
    ) | Permission.objects.filter(
        content_type=historico_ct,
        codename__in=["view_historico"],
    )

    # .set() sincroniza exatamente as permissões desejadas para o grupo
    grupo_usuario_comum.permissions.set(permissoes_usuario_comum)
    grupo_tecnico.permissions.set(permissoes_tecnico)