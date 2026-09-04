from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from .forms import ComentarioForm
from .models import Ticket, Ativo, Comentario

# Create your views here.

class TicketListView(generic.ListView):
    model = Ticket

# class TicketDetailView(generic.DetailView):
#     model = Ticket

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