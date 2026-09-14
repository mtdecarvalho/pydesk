from django.urls import path
from tickets import views

urlpatterns = [
    path('', views.index, name="index"),
    path('tickets/', views.TicketsHomeView, name="tickets"),
    path('tickets/meus_tickets', views.MeusTicketsView, name="meus_tickets"),
    path('tickets/encerrados', views.TicketsEncerradosView, name="tickets_encerrados"),
    path('tickets/cancelados', views.TicketsCanceladosView, name="tickets_cancelados"),
    path('tickets/abertos', views.TicketsAbertosView, name="tickets_abertos"),
    path('tickets/nao_alocados', views.TicketsNaoAlocadosView, name="tickets_nao_alocados"),
    path('tickets/criar', views.CriarTicketView, name="criar_ticket"),
    #path('tickets/<int:pk>', views.TicketDetailView.as_view(), name="ticket-detail"),
    path('tickets/<int:pk>/', views.TicketDetalheView, name="ticket_detalhe"),
    path('tickets/<int:pk>/encerrar', views.EncerrarTicketView, name="encerrar_ticket"),
    path('tickets/<int:pk>/cancelar', views.CancelarTicketView, name="cancelar_ticket"),
]
