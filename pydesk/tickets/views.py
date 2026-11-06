from datetime import datetime

from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from .forms import CancelarTicketForm, ComentarioForm, CriarTicketForm, EncerrarTicketForm, TicketEmEsperaForm
from .models import Ticket, Comentario

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Create your views here.

class TicketListView(generic.ListView):
    model = Ticket


def processar_email(ticket, tipo, comentario=None):
    recipient_list = []
    # Cria uma lista vazia para guardar os endereços de email

    tecnicos = Group.objects.get(name__iexact="TECNICOS").user_set.all()
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
        subject=f"[PyDesk] Novo Ticket Registrado #{ticket.id} - {ticket.titulo}"
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
        subject=f"[PyDesk] Novo Comentário no Ticket #{ticket.id} - {ticket.titulo}"
        template = 'emails/novo_comentario.html'

        if ticket.tecnico:
            recipient_list.append(ticket.tecnico.email)
            # Se houver um técnico alocado a este ticket, envia o email somente a ele e ao solicitante.
        else:
            for tecnico in tecnicos:
                if tecnico.email:
                    recipient_list.append(tecnico.email)
                    # Adiciona o email de todos os técnicos a lista de destinatarios
    
    elif tipo == "TICKET_ENCERRADO":
        context = {
            "ticket": ticket,
            "comentario": comentario,
        }
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} Encerrado"
        template = 'emails/ticket_encerrado.html'
        recipient_list.append(ticket.tecnico.email)

    elif tipo == "TICKET_CANCELADO":
        context = {
            "ticket": ticket,
            "comentario": comentario,
        }
        subject=f"[PyDesk] Ticket #{ticket.id} - {ticket.titulo} Cancelado"
        template = 'emails/ticket_cancelado.html'
        if ticket.tecnico:
            recipient_list.append(ticket.tecnico.email)
        else:
            for tecnico in tecnicos:
                if tecnico.email:
                    recipient_list.append(tecnico.email)
    
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

    

@login_required
def TicketsHomeView(request):
    qtd_tickets = Ticket.objects.all().count()
    qtd_tickets_abertos = Ticket.objects.all().filter(estado__exact="AB").count()
    qtd_tickets_encerrados = Ticket.objects.all().filter(estado__exact="EN").count()
    qtd_tickets_cancelados = Ticket.objects.all().filter(estado__exact="CC").count()

    context = {
        "qtd_tickets": qtd_tickets,
        "qtd_tickets_abertos": qtd_tickets_abertos,
        "qtd_tickets_encerrados": qtd_tickets_encerrados,
        "qtd_tickets_cancelados": qtd_tickets_cancelados,
    }

    return render(request, "tickets_home.html", context=context)

@login_required
def MeusTicketsView(request):
    if request.user.has_perm('tickets.pode_encerrar'):
        lista_tickets = Ticket.objects.filter(tecnico=request.user).filter(estado="EA")
    elif request.user.has_perm('tickets.pode_cancelar'):
        lista_tickets = Ticket.objects.filter(solicitante=request.user).exclude(estado="CC").exclude(estado="EN")
    else:
        lista_tickets = None

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Meus tickets",
        "aba": "Meus tickets"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsEncerradosView(request):
    lista_tickets = Ticket.objects.filter(estado="EN")

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Encerrados",
        "aba": "Tickets encerrados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_cancelar')
def TicketsCanceladosView(request):
    if request.user.is_superuser:
        lista_tickets = Ticket.objects.filter(estado="CC")
        # Permite que o admin veja todos os tickets cancelados
    else:
        lista_tickets = Ticket.objects.filter(solicitante=request.user).filter(estado="CC")
        # Se o usuario nao for adm, limita a visualização para tickets cancelados apenas por ele

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Cancelados",
        "aba": "Tickets cancelados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsAbertosView(request):
    lista_tickets = Ticket.objects.filter(estado="AB")

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Abertos",
        "aba": "Tickets abertos"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsNaoAlocadosView(request):
    lista_tickets = Ticket.objects.filter(estado="AB").filter(tecnico=None)

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets não alocados",
        "aba": "Tickets não alocados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
def TicketsEmEsperaView(request):
    if request.user.has_perm('pode_cancelar'):
        lista_tickets = Ticket.objects.filter(solicitante=request.user).filter(estado="EE")
    else:
        lista_tickets = Ticket.objects.filter(estado="EE")

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Em Espera",
        "aba": "Tickets em espera"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
def TicketDetalheView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        if "submit_comentario" in request.POST:
            comentario_form = ComentarioForm(request.POST, prefix='comentario')

            if comentario_form.is_valid():
                comentario = comentario_form.cleaned_data['comentario']
                id_ticket = ticket
                usuario = request.user
                comentario = Comentario(comentario=comentario, id_ticket=id_ticket, usuario=usuario)
                comentario.save()

                if ticket.estado == "EE":
                    ticket.estado = "AB"
                ticket.save()

                #processar_email(
                #    ticket=ticket,
                #    comentario=comentario,
                #    tipo="NOVO_COMENTARIO"
                #)

                return redirect('ticket_detalhe', pk=pk)
        elif "alocar_ticket" in request.POST:
            comentario_form = ComentarioForm(prefix='comentario')

            tecnico = request.user
            ticket.tecnico = tecnico
            ticket.estado = "EA"

            comentario = f"Ticket alocado para a fila de {tecnico.first_name} {tecnico.last_name}."
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)

            ticket.save()
            comentario.save()

            return redirect('ticket_detalhe', pk=pk)
        elif "desalocar_ticket" in request.POST:
            comentario_form = ComentarioForm(prefix='comentario')

            comentario = f"Ticket desalocado da fila de {ticket.tecnico.first_name} {ticket.tecnico.last_name}."
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            ticket.tecnico = None
            ticket.estado = "AB"
            ticket.save()

            
        elif "cancelar_ticket" in request.POST:
            comentario_form = ComentarioForm(prefix='comentario')

            comentario = f"Ticket cancelado por {ticket.solicitante.first_name} {ticket.solicitante.last_name}."
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            ticket.tecnico = None
            ticket.estado = "CC"

            ticket.save()

        elif "alterar_prioridade" in request.POST:
            ticket.prioridade = request.POST.get("prioridade")
            comentario_form = ComentarioForm(prefix='comentario')
            comentario = f"Prioridade alterada por {ticket.tecnico} para {ticket.prioridade}."
            ticket.save()

    else:
        comentario_form = ComentarioForm(initial={"comentario": ""}, prefix="comentario")

    context = {
        'comentario_form': comentario_form,
        'ticket': ticket
    }

    return render(request, "ticket_detalhe.html", context=context)

@login_required
@permission_required('tickets.pode_cancelar')
def CriarTicketView(request):
    if request.method == 'POST':
        form = CriarTicketForm(request.POST)

        if form.is_valid():
            categoria = form.cleaned_data['categoria']
            prioridade = form.cleaned_data['prioridade']
            titulo = form.cleaned_data['titulo']
            descricao = form.cleaned_data['descricao']
            solicitante = request.user

            ticket = Ticket(categoria=categoria,
                            prioridade=prioridade,
                            titulo=titulo,
                            descricao=descricao,
                            solicitante=solicitante)
            
            ticket.save()

            comentario = f"Ticket criado por {ticket.solicitante.first_name} {ticket.solicitante.last_name}."
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            processar_email(
                ticket=ticket,
                tipo="NOVO_TICKET"
            )

            return redirect(ticket.get_absolute_url())

    else:
        form = CriarTicketForm()

    context = {
        'form': form
    }

    return render(request, 'criar_ticket.html', context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def EncerrarTicketView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = EncerrarTicketForm(request.POST)

        if form.is_valid():
            solucao = form.cleaned_data['solucao']

            ticket.solucao = solucao
            ticket.estado = "EN"
            ticket.data_encerramento = datetime.now()
            ticket.save()

            comentario = f"Ticket encerrado por {ticket.tecnico.first_name} {ticket.tecnico.last_name}. Solução: {ticket.solucao}"
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            processar_email(
                ticket=ticket,
                comentario=comentario,
                tipo="TICKET_ENCERRADO"
            )

            return redirect(ticket.get_absolute_url())

    else:
        form = EncerrarTicketForm()

    context = {
        'form': form,
        'ticket': ticket,
    }

    return render(request, 'encerrar_ticket.html', context=context)

@login_required
@permission_required('tickets.pode_cancelar')
def CancelarTicketView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = CancelarTicketForm(request.POST)

        if form.is_valid():
            motivo_cancelamento = form.cleaned_data['motivo_cancelamento']

            ticket.motivo_cancelamento = motivo_cancelamento
            ticket.estado = "CC"
            ticket.data_encerramento = datetime.now()
            ticket.save()

            comentario = f"Ticket cancelado por {ticket.solicitante.first_name} {ticket.solicitante.last_name}. Motivo: {ticket.motivo_cancelamento}"
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            processar_email(
                ticket=ticket,
                comentario=comentario,
                tipo="TICKET_CANCELADO"
            )

            return redirect(ticket.get_absolute_url())

    else:
        form = CancelarTicketForm()

    context = {
        'form': form,
        'ticket': ticket,
    }

    return render(request, 'cancelar_ticket.html', context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketEmEsperaView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = TicketEmEsperaForm(request.POST)

        if form.is_valid():
            ticket.tecnico = None
            ticket.estado = "EE"
            ticket.save()

            comentario = f"Este ticket está em espera, aguardando uma ação sua. Motivo: {form.cleaned_data['comentario']}"
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            #processar_email(
            #    ticket=ticket,
            #    comentario=comentario,
            #    tipo="TICKET_CANCELADO"
            #)

            return redirect(ticket.get_absolute_url())

    else:
        form = TicketEmEsperaForm()

    context = {
        'form': form,
        'ticket': ticket
    }

    return render(request, 'em_espera_ticket.html', context=context)

def index(request):
    '''Função de view da página de índice do PyDesk'''

    return render(request, "index.html")