from django.contrib import admin
from django.urls import path
from tickets import views

urlpatterns = [
    path('', views.index, name="index"),
    path('tickets/', views.TicketsHomeView, name="tickets"),
    path('tickets/meus_tickets', views.MeusTicketsView, name="meus_tickets"),
    path('tickets/todos_tickets', views.TodosTicketsView, name="todos_tickets"),
    path('tickets/encerrados', views.TicketsEncerradosView, name="tickets_encerrados"),
    path('tickets/cancelados', views.TicketsCanceladosView, name="tickets_cancelados"),
    path('tickets/abertos', views.TicketsAbertosView, name="tickets_abertos"),
    path('tickets/em_espera', views.TicketsEmEsperaView, name="tickets_em_espera"),
    path('tickets/nao_alocados', views.TicketsNaoAlocadosView, name="tickets_nao_alocados"),
    path('tickets/criar', views.CriarTicketView, name="criar_ticket"),
    path('tickets/<int:pk>/', views.TicketDetalheView, name="ticket_detalhe"),
    path('tickets/<int:pk>/historico/', views.TicketHistoricoView, name="ticket_historico"),
    path('tickets/<int:pk>/encerrar', views.EncerrarTicketView, name="encerrar_ticket"),
    path('tickets/<int:pk>/cancelar', views.CancelarTicketView, name="cancelar_ticket"),
    path('tickets/<int:pk>/em_espera', views.TicketEmEsperaView, name="em_espera_ticket"),
]
