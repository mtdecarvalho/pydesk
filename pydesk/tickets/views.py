from django.shortcuts import render
from django.views import generic
from .models import Ticket, Ativo

# Create your views here.

class TicketListView(generic.ListView):
    model = Ticket

class TicketDetailView(generic.DetailView):
    model = Ticket

class AtivoListView(generic.ListView):
    model = Ativo

class AtivoDetailView(generic.DetailView):
    model = Ativo

def index(request):
    '''Função de view da página de índice do PyDesk'''

    qtd_tickets = Ticket.objects.all().count()
    qtd_tickets_abertos = Ticket.objects.all().filter(estado__exact="AB").count()
    qtd_tickets_encerrados = Ticket.objects.all().filter(estado__exact="EN").count()
    qtd_tickets_cancelados = Ticket.objects.all().filter(estado__exact="CC").count()

    qtd_ativos = Ativo.objects.all().count()

    context = {
        "qtd_tickets": qtd_tickets,
        "qtd_tickets_abertos": qtd_tickets_abertos,
        "qtd_tickets_encerrados": qtd_tickets_encerrados,
        "qtd_tickets_cancelados": qtd_tickets_cancelados,
        "qtd_ativos": qtd_ativos
    }

    return render(request, "index.html", context=context)