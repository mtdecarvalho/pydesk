from datetime import datetime

from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from .forms import ComentarioForm, CriarTicketForm, EncerrarTicketForm
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
    lista_tickets = Ticket.objects.filter(tecnico=request.user).filter(estado="AB")

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
    lista_tickets = Ticket.objects.filter(tecnico=None)

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Não Alocados",
        "aba": "Tickets Não Alocados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

# class TicketDetailView(generic.DetailView):
#     model = Ticket

@login_required
def TicketDetailView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':

        form = ComentarioForm(request.POST)

        if form.is_valid():
            comentario = form.cleaned_data['comentario']
            id_ticket = ticket
            usuario = request.user
            comentario = Comentario(comentario=comentario, id_ticket=id_ticket, usuario=usuario)
            comentario.save()

            return redirect('ticket-detail', pk=pk)

    else:
        form = ComentarioForm(initial={"comentario": ""})

    context = {
        'form': form,
        'ticket': ticket
    }

    return render(request, "ticket_detail.html", context=context)

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

            ticket = Ticket(categoria=categoria,
                            prioridade=prioridade,
                            titulo=titulo,
                            descricao=descricao)
            
            ticket.save()
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
            return redirect(ticket.get_absolute_url())

    else:
        form = EncerrarTicketForm()

    context = {
        'form': form
    }

    return render(request, 'encerrar_ticket.html', context=context)

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