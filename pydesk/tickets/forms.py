from django import forms

class ComentarioForm(forms.Form):
    comentario = forms.CharField(help_text="Insira seu comentário.")