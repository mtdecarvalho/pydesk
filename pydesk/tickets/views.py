from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_GET
from django.core.exceptions import PermissionDenied


from .forms import CancelarTicketForm, ComentarioForm, CriarTicketForm, EncerrarTicketForm, TicketEmEsperaForm
from .models import Ticket, Comentario, Historico
from .utils import processar_email

from django.contrib.auth.decorators import login_required, permission_required, user_passes_test

# Create your views here.

class TicketListView(generic.ListView):
    model = Ticket    

def eh_superuser(user):
    return user.is_superuser

def eh_tecnico_ou_admin(user):
    return user.is_superuser or user.has_perm("tickets.pode_encerrar")

def pode_acessar_ticket(user, ticket):
    if user.is_superuser or user.has_perm("tickets.pode_encerrar"):
        return True
    return ticket.solicitante_id == user.pk

@login_required
def TicketsHomeView(request):
    qtd_tickets = Ticket.objects.all().count()
    qtd_tickets_abertos = Ticket.objects.all().filter(estado__exact=Ticket.EscolhaEstado.ABERTO).count()
    qtd_tickets_encerrados = Ticket.objects.all().filter(estado__exact=Ticket.EscolhaEstado.ENCERRADO).count()
    qtd_tickets_cancelados = Ticket.objects.all().filter(estado__exact=Ticket.EscolhaEstado.CANCELADO).count()
    qtd_tickets_em_andamento = Ticket.objects.all().filter(estado__exact=Ticket.EscolhaEstado.EM_ANDAMENTO).count()
    qtd_tickets_em_espera = Ticket.objects.all().filter(estado__exact=Ticket.EscolhaEstado.EM_ESPERA).count()

    context = {
        "qtd_tickets": qtd_tickets,
        "qtd_tickets_abertos": qtd_tickets_abertos,
        "qtd_tickets_encerrados": qtd_tickets_encerrados,
        "qtd_tickets_cancelados": qtd_tickets_cancelados,
        "qtd_tickets_em_andamento": qtd_tickets_em_andamento,
        "qtd_tickets_em_espera": qtd_tickets_em_espera,
    }

    return render(request, "tickets_home.html", context=context)

@login_required
def MeusTicketsView(request):
    if request.user.has_perm('tickets.pode_encerrar'):
        lista_tickets = Ticket.objects.filter(tecnico=request.user).filter(estado=Ticket.EscolhaEstado.EM_ANDAMENTO)
    elif request.user.has_perm('tickets.pode_cancelar'):
        lista_tickets = Ticket.objects.filter(solicitante=request.user).exclude(estado=Ticket.EscolhaEstado.CANCELADO).exclude(estado=Ticket.EscolhaEstado.ENCERRADO)
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
    lista_tickets = Ticket.objects.filter(estado=Ticket.EscolhaEstado.ENCERRADO)

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
        lista_tickets = Ticket.objects.filter(estado=Ticket.EscolhaEstado.CANCELADO)
        # Permite que o admin veja todos os tickets cancelados
    else:
        lista_tickets = Ticket.objects.filter(solicitante=request.user).filter(estado=Ticket.EscolhaEstado.CANCELADO)
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
    lista_tickets = Ticket.objects.filter(estado=Ticket.EscolhaEstado.ABERTO)

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Abertos",
        "aba": "Tickets abertos"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
@permission_required('tickets.pode_encerrar')
def TicketsNaoAlocadosView(request):
    lista_tickets = Ticket.objects.filter(estado=Ticket.EscolhaEstado.ABERTO).filter(tecnico=None)

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets não alocados",
        "aba": "Tickets não alocados"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
def TicketsEmEsperaView(request):
    if request.user.has_perm('tickets.pode_cancelar'):
        lista_tickets = Ticket.objects.filter(solicitante=request.user).filter(estado=Ticket.EscolhaEstado.EM_ESPERA)
    else:
        lista_tickets = Ticket.objects.filter(estado=Ticket.EscolhaEstado.EM_ESPERA)

    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Tickets Em Espera",
        "aba": "Tickets em espera"
    }

    return render(request, "lista_tickets_generica.html", context=context)

@login_required
def TicketDetalheView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if not pode_acessar_ticket(request.user, ticket):
        raise PermissionDenied("Você não tem permissão para visualizar este ticket.")

    if request.method == 'POST':

        if "submit_comentario" in request.POST:
            comentario_form = ComentarioForm(request.POST, prefix='comentario')

            if comentario_form.is_valid():
                comentario = comentario_form.cleaned_data['comentario']

                with transaction.atomic():
                    ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                    if not pode_acessar_ticket(request.user, ticket_locked):
                        raise PermissionDenied("Você não tem permissão para comentar neste ticket.")

                    Comentario.objects.create(comentario=comentario, ticket=ticket_locked, usuario=request.user)

                    # Gera um novo registro no histórico
                    Historico.objects.create(
                        ticket=ticket_locked,
                        usuario=request.user,
                        tipo=Historico.TipoAcao.COMENTARIO,
                    )

                    # Reabre o ticket se estiver em espera
                    if ticket_locked.estado == Ticket.EscolhaEstado.EM_ESPERA:
                        ticket_locked.estado = Ticket.EscolhaEstado.ABERTO
                        ticket_locked.save()

                        Historico.objects.create(
                            ticket=ticket_locked,
                            usuario=None,
                            tipo=Historico.TipoAcao.ESTADO
                        )
                    else:
                        ticket_locked.save()

                processar_email(
                    ticket=ticket,
                    comentario=comentario,
                    tipo="NOVO_COMENTARIO"
                )

                return redirect('ticket_detalhe', pk=pk)
            
        elif "alocar_ticket" in request.POST:
            if not eh_tecnico_ou_admin(request.user):
                raise PermissionDenied("Apenas técnicos podem alocar tickets.")

            with transaction.atomic():
                ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                ticket_locked.tecnico = request.user
                ticket_locked.estado = Ticket.EscolhaEstado.EM_ANDAMENTO
                ticket_locked.save()

                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=request.user,
                    tipo=Historico.TipoAcao.TECNICO
                )

                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=None,
                    tipo=Historico.TipoAcao.ESTADO
                )

            processar_email(
                ticket=ticket_locked,
                tipo="TICKET_EM_ANDAMENTO"
            )

            return redirect('ticket_detalhe', pk=pk)
        
        elif "desalocar_ticket" in request.POST:
            if not eh_tecnico_ou_admin(request.user):
                raise PermissionDenied("Apenas técnicos podem desalocar tickets.")

            with transaction.atomic():
                ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                ticket_locked.tecnico = None
                ticket_locked.estado = Ticket.EscolhaEstado.ABERTO
                ticket_locked.save()

                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=request.user,
                    tipo=Historico.TipoAcao.TECNICO
                )
                
                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=None,
                    tipo=Historico.TipoAcao.ESTADO
                )

            return redirect('ticket_detalhe', pk=pk)


        elif "alterar_prioridade" in request.POST:
            if not eh_tecnico_ou_admin(request.user):
                raise PermissionDenied("Apenas técnicos podem alterar a prioridade.")
            
            nova_prioridade = request.POST.get("prioridade")
            prioridades_validas = dict(Ticket.EscolhaPrioridade.choices)

            if nova_prioridade not in prioridades_validas:
                raise PermissionDenied("Prioridade inválida.")

            with transaction.atomic():
                ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                ticket_locked.prioridade = nova_prioridade
                ticket_locked.save()

                Historico.objects.create(
                    ticket=ticket,
                    usuario=request.user,
                    tipo=Historico.TipoAcao.PRIORIDADE
                )

            return redirect('ticket_detalhe', pk=pk)

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

            Historico.objects.create(
                ticket=ticket,
                usuario=request.user,
                tipo=Historico.TipoAcao.CRIACAO
            )

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
@permission_required('tickets.pode_encerrar', raise_exception=True)
def EncerrarTicketView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = EncerrarTicketForm(request.POST)

        if form.is_valid():
            solucao = form.cleaned_data['solucao']

            with transaction.atomic():
                ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                ticket_locked.solucao = solucao
                ticket_locked.estado = Ticket.EscolhaEstado.ENCERRADO
                ticket_locked.data_encerramento = timezone.now()
                ticket_locked.save()

                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=request.user,
                    tipo=Historico.TipoAcao.ENCERRAMENTO
                )

            processar_email(
                ticket=ticket_locked,
                comentario=ticket_locked.solucao,
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
@permission_required('tickets.pode_cancelar', raise_exception=True)
def CancelarTicketView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if not pode_acessar_ticket(request.user, ticket):
        raise PermissionDenied("Você não tem permissão para cancelar este ticket.")

    if request.method == 'POST':
        form = CancelarTicketForm(request.POST)

        if form.is_valid():
            motivo_cancelamento = form.cleaned_data['motivo_cancelamento']

            with transaction.atomic():
                ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                ticket_locked.motivo_cancelamento = motivo_cancelamento
                ticket_locked.estado = Ticket.EscolhaEstado.CANCELADO
                ticket_locked.data_encerramento = timezone.now()
                ticket_locked.save()

                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=request.user,
                    tipo=Historico.TipoAcao.CANCELAMENTO
                )

            processar_email(
                ticket=ticket_locked,
                comentario=ticket_locked.motivo_cancelamento,
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
@permission_required('tickets.pode_encerrar', raise_exception=True)
def TicketEmEsperaView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = TicketEmEsperaForm(request.POST)

        if form.is_valid():
            comentario = form.cleaned_data['comentario']

            with transaction.atomic():
                ticket_locked = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
                usuario = ticket_locked.tecnico
                Comentario.objects.create(comentario=comentario,usuario=usuario, ticket=ticket_locked)

                ticket_locked.tecnico = None
                ticket_locked.estado = Ticket.EscolhaEstado.EM_ESPERA
                ticket_locked.save()

                Historico.objects.create(
                    ticket=ticket_locked,
                    usuario=request.user,
                    tipo=Historico.TipoAcao.ESTADO
                )

            processar_email(
                ticket=ticket_locked,
                comentario=comentario,
                tipo="TICKET_EM_ESPERA"
            )

            return redirect(ticket.get_absolute_url())

    else:
        form = TicketEmEsperaForm()

    context = {
        'form': form,
        'ticket': ticket
    }

    return render(request, 'em_espera_ticket.html', context=context)

@login_required
@permission_required("tickets.view_historico", raise_exception=True)
@require_GET
def TicketHistoricoView(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not pode_acessar_ticket(request.user, ticket):
        raise PermissionDenied("Você não tem permissão para ver o histórico deste ticket.")
    
    historicos = Historico.objects.filter(ticket=ticket).select_related("usuario").order_by("-data", "-pk")

    return render(
        request,
        "historico_ticket.html",
        {"ticket": ticket, "historicos": historicos},
    )

@login_required
@user_passes_test(eh_superuser)
def TodosTicketsView(request):
    lista_tickets = Ticket.objects.all()
    
    context = {
        "lista_tickets": lista_tickets,
        "titulo": "Pydesk - Todos tickets",
        "aba": "Todos tickets"
    }

    return render(request, "lista_tickets_generica.html", context=context)


def index(request):
    '''Função de view da página de índice do PyDesk'''

    return render(request, "index.html")