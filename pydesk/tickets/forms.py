from django import forms
from django.forms.models import ModelForm

from autenticacao.models import Usuario

from .models import Comentario, Ticket

class ComentarioForm(ModelForm):
    class Meta:
        model = Comentario
        fields = ["comentario"]

class CriarTicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["categoria", "prioridade", "titulo", "descricao"]

class EncerrarTicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["solucao"]

class CancelarTicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["motivo_cancelamento"]