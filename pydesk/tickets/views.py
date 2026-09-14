from datetime import datetime

from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from autenticacao.models import Usuario

from .forms import CancelarTicketForm, ComentarioForm, CriarTicketForm, EncerrarTicketForm
from .models import Ticket, Comentario

from django.contrib.auth.decorators import login_required, permission_required

# Create your views here.

class TicketListView(generic.ListView):
    model = Ticket

@login_required
def TicketsHomeView(request):
    return render(request, "tickets_home.html")

@login_required
def MeusTicketsView(request):
    if request.user.has_perm('tickets.pode_encerrar'):
        lista_tickets = Ticket.objects.filter(tecnico=request.user).filter(estado="AB")
    elif request.user.has_perm('tickets.pode_cancelar'):
        lista_tickets = Ticket.objects.filter(solicitante=request.user).filter(estado="AB")
    else:
        lista_tickets = None

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Meus Tickets",
        "aba": "Meus Tickets"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsEncerradosView(request):
    lista_tickets = Ticket.objects.filter(estado="EN")

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Encerrados",
        "aba": "Tickets Encerrados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_cancelar')
def TicketsCanceladosView(request):
    lista_tickets = Ticket.objects.filter(solicitante=request.user).filter(estado="CC")

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Cancelados",
        "aba": "Tickets Cancelados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsAbertosView(request):
    lista_tickets = Ticket.objects.filter(estado="AB")

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Abertos",
        "aba": "Tickets Abertos"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsNaoAlocadosView(request):
    lista_tickets = Ticket.objects.filter(estado="AB").filter(tecnico=None)

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Não Alocados",
        "aba": "Tickets Não Alocados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

# class TicketDetailView(generic.DetailView):
#     model = Ticket

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
                ticket.save()

                return redirect('ticket_detalhe', pk=pk)
        elif "alocar_ticket" in request.POST:
            comentario_form = ComentarioForm(prefix='comentario')

            tecnico = request.user
            ticket.tecnico = tecnico

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
            ticket.save()

            
        elif "cancelar_ticket" in request.POST:
            comentario_form = ComentarioForm(prefix='comentario')

            comentario = f"Ticket cancelado por {ticket.solicitante.first_name} {ticket.solicitante.last_name}."
            comentario = Comentario(comentario=comentario, id_ticket=ticket, usuario=None)
            comentario.save()

            ticket.tecnico = None
            ticket.estado = "CC"

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

            return redirect(ticket.get_absolute_url())

    else:
        form = EncerrarTicketForm()

    context = {
        'form': form
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

            return redirect(ticket.get_absolute_url())

    else:
        form = CancelarTicketForm()

    context = {
        'form': form
    }

    return render(request, 'cancelar_ticket.html', context=context)

def index(request):
    '''Função de view da página de índice do PyDesk'''

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

    return render(request, "index.html", context=context)