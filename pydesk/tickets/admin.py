from django import forms
from django.contrib import admin
from .models import Ticket, Comentario, Historico

# Register your models here.

class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        solucao = cleaned_data.get('solucao')
        motivo_cancelamento = cleaned_data.get('motivo_cancelamento')
        tecnico = cleaned_data.get('tecnico')

        # Regra 1: Se o estado for Encerrado, exige solução
        if estado == Ticket.EscolhaEstado.ENCERRADO:
            if not solucao or not solucao.strip():
                self.add_error('solucao', 'O preenchimento da solução é obrigatório para tickets encerrados.')

        # Regra 2: Se o estado for Cancelado, exige o motivo
        if estado == Ticket.EscolhaEstado.CANCELADO:
            if not motivo_cancelamento or not motivo_cancelamento.strip():
                self.add_error('motivo_cancelamento', 'O motivo do cancelamento é obrigatório.')


        return cleaned_data

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm

    list_display = ['id', 'titulo', 'estado', 'tecnico', 'solicitante']

    fields = ['titulo', 'descricao', 'estado', 'data_criacao', 'data_ultima_atualizacao', 'data_encerramento', 'tecnico', 'solucao', 'motivo_cancelamento']

    readonly_fields = [
        'data_criacao', 
        'data_ultima_atualizacao',
        'data_encerramento'
    ]

    class Media:
        js = ('tickets/js/ticket_admin.js',)

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'data', 'comentario', 'usuario']

@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'data', 'usuario', 'tipo', 'acao']

    readonly_fields = ['id', 'ticket', 'data', 'usuario', 'tipo', 'acao']

    def has_add_permission(self, request):
        return False

    # 2. Impede a edição de registros existentes
    def has_change_permission(self, request, obj=None):
        return False

    # 3. Impede a exclusão de registros (opcional, mas recomendado para auditoria)
    def has_delete_permission(self, request, obj=None):
        return False