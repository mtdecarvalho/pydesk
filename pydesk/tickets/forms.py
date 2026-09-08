from django import forms

from .models import Ticket

class ComentarioForm(forms.Form):
    comentario = forms.CharField(help_text="Insira seu comentário.")

class CriarTicketForm(forms.Form):
    categoria = forms.ChoiceField(choices=Ticket.ESCOLHA_CATEGORIA,
                                  initial="HARDWARE")
    prioridade = forms.ChoiceField(choices=Ticket.ESCOLHA_PRIORIDADE,
                                   initial="BAIXA")
    titulo = forms.CharField(help_text="Insira o titulo do seu ticket.")
    descricao = forms.CharField(help_text="Descreva em detalhes a sua solicitação.")

class EncerrarTicketForm(forms.Form):
    solucao = forms.CharField(help_text="Descreva em detalhes o que foi feito para solucionar este ticket.")