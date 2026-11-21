import logging

from django.contrib.auth.models import Group

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

def _obter_emails_tecnicos():
    grupo_tecnico = Group.objects.filter(name__iexact="TECNICO").first()
    if not grupo_tecnico:
        return []
    return list(
        grupo_tecnico.user_set.exclude(email="")
        .exclude(email__isnull=True)
        .values_list("email", flat=True)
    )

def processar_email(ticket, tipo, comentario=None):
    destinatarios = []
    # Cria uma lista vazia para guardar os endereços de email

    def adicionar_email(endereco):
        if endereco and endereco not in destinatarios:
            destinatarios.append(endereco)

    if ticket.solicitante and ticket.solicitante.email:
        adicionar_email(ticket.solicitante.email)
        # Adiciona o email do solicitante (criador do ticket) na lista

    context = {"ticket": ticket}
    if comentario is not None:
        context["comentario"] = comentario
    
    if tipo == "NOVO_TICKET":
        subject=f"[PyDesk] Novo ticket registrado #{ticket.id} - {ticket.titulo}"
        template = 'emails/novo_ticket.html'

        # Manda email a todos os tecnicos
        for email_tecnico in _obter_emails_tecnicos():
            adicionar_email(email_tecnico)

    elif tipo == "NOVO_COMENTARIO":
        subject=f"[PyDesk] Novo comentário no ticket #{ticket.id} - {ticket.titulo}"
        template = 'emails/novo_comentario.html'

        if ticket.tecnico and ticket.tecnico.email:
            adicionar_email(ticket.tecnico.email)
            # Se houver um técnico alocado a este ticket, envia o email somente a ele e ao solicitante.
        else:
            for email_tecnico in _obter_emails_tecnicos():
                adicionar_email(email_tecnico)
                # Adiciona o email de todos os técnicos a lista de destinatarios

    elif tipo == "TICKET_EM_ANDAMENTO":
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} está em andamento"
        template = 'emails/ticket_em_andamento.html'
    
    elif tipo == "TICKET_ENCERRADO":
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} encerrado"
        template = 'emails/ticket_encerrado.html'
        if ticket.tecnico and ticket.tecnico.email:
            adicionar_email(ticket.tecnico.email)

    elif tipo == "TICKET_CANCELADO":
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} cancelado"
        template = 'emails/ticket_cancelado.html'
        
        for email_tecnicos in _obter_emails_tecnicos():
            adicionar_email(email_tecnicos)

    elif tipo == "TICKET_EM_ESPERA":
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} está em espera"
        template = 'emails/ticket_em_espera.html'

    else:
        logger.warning("Tipo de e-mail desconhecido recebido em processar_email: %s", tipo)
        return

    if not destinatarios:
        return

    html_message = render_to_string(template, context)
    plain_text_content = strip_tags(html_message)
    # O email é enviado em HTML, o plain text é só um fallback caso a opção acima não seja suportada. O ideal é que seja.

    try:
        send_mail(
            subject=subject,
            message=plain_text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatarios,
            html_message=html_message,
            fail_silently=False, # Defina como True em produção se não quiser travar em erros SMTP
        )
    except Exception as e:
        logger.exception("Erro ao enviar e-mail (%s) para o ticket #%s", tipo, ticket.pk)