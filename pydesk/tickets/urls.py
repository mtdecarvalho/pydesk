from django.urls import path
from tickets import views

urlpatterns = [
    path('', views.index, name="index"),
    path('tickets/', views.TicketListView.as_view(), name="tickets"),
    path('tickets/<int:pk>', views.TicketDetailView.as_view(), name="ticket-detail"),
    path('ativos/', views.AtivoListView.as_view(), name="ativos"),
    path('ativos/<uuid:pk>', views.AtivoDetailView.as_view(), name="ativo-detail"),
]
