from django.contrib.auth.models import Group

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def processar_email(ticket, tipo, comentario=None):
    recipient_list = []
    # Cria uma lista vazia para guardar os endereços de email

    tecnicos = Group.objects.get(name__iexact="TECNICO").user_set.all()
    # Busca todos os técnicos, pesquisando os usuarios cadastrados no grupo de técnicos.
    # Necessário na criação pois o ticket não é alocado a nenhum técnico na sua criação.
    # Pode ser usado também no cancelamento.

    if ticket.solicitante and ticket.solicitante.email:
        recipient_list.append(ticket.solicitante.email)
        # Adiciona o email do solicitante (criador do ticket) na lista

    if tipo == "NOVO_TICKET":
        context = {
            "ticket": ticket
        }
        subject=f"[PyDesk] Novo ticket registrado #{ticket.id} - {ticket.titulo}"
        template = 'emails/novo_ticket.html'

        for tecnico in tecnicos:
            if tecnico.email:
                recipient_list.append(tecnico.email)
                # Adiciona o email de todos os técnicos a lista de destinatarios

    elif tipo == "NOVO_COMENTARIO":
        context = {
            "ticket": ticket,
            "comentario": comentario,
        }
        subject=f"[PyDesk] Novo comentário no ticket #{ticket.id} - {ticket.titulo}"
        template = 'emails/novo_comentario.html'

        if ticket.tecnico:
            recipient_list.append(ticket.tecnico.email)
            # Se houver um técnico alocado a este ticket, envia o email somente a ele e ao solicitante.
        else:
            for tecnico in tecnicos:
                if tecnico.email:
                    recipient_list.append(tecnico.email)
                    # Adiciona o email de todos os técnicos a lista de destinatarios

    elif tipo == "TICKET_EM_ANDAMENTO":
            context = {
                "ticket": ticket
            }
            subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} está em andamento"
            template = 'emails/ticket_em_andamento.html'
    
    elif tipo == "TICKET_ENCERRADO":
        context = {
            "ticket": ticket,
            "comentario": comentario,
        }
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} encerrado"
        template = 'emails/ticket_encerrado.html'
        recipient_list.append(ticket.tecnico.email)

    elif tipo == "TICKET_CANCELADO":
        context = {
            "ticket": ticket,
            "comentario": comentario,
        }
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} cancelado"
        template = 'emails/ticket_cancelado.html'
        
        for tecnico in tecnicos:
            if tecnico.email:
                recipient_list.append(tecnico.email)

    elif tipo == "TICKET_EM_ESPERA":
        context = {
            "ticket": ticket,
            "comentario": comentario,
        }
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} está em espera"
        template = 'emails/ticket_em_espera.html'
    
    if recipient_list:
        # Checa primeiro se há uma lista de destinatários antes de enviar o email.
        html_message = render_to_string(template, context)
        plain_text_content = strip_tags(html_message)
        # O email é enviado em HTML, o plain text é só um fallback caso a opção acima não seja suportada. O ideal é que seja.

        try:
            send_mail(
                subject=subject,
                message=plain_text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False, # Defina como True em produção se não quiser travar em erros SMTP
            )
        except Exception as e:
            print(f'Erro ao enviar email: {e}')