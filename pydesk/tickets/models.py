from datetime import datetime

from django.db import models
from django.urls import reverse
from django.utils import timezone
from pydesk.settings import AUTH_USER_MODEL as Usuario

# Create your models here.

class Ticket(models.Model):
    '''
    Modelo usado para representar um ticket.\n
    data_criacao -> datetime\n
    data_encerramento -> datetime\n
    data_ultima_atualizacao -> datetime\n
    categoria -> CharField, choices = ESCOLHA_CATEGORIA\n
    prioridade -> CharField, choices = ESCOLHA_PRIORIDADE\n
    estado -> CharField, choices = ESCOLHA_ESTADO\n
    titulo -> CharField\n
    descricao -> TextField\n
    solucao -> TextField\n
    tecnico -> ForeignKey, modelo "Usuario"\n
    '''
    # DATAS USADAS NO TICKET

    # Gerada automaticamente na abertura
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        null=False,
        verbose_name="Data da criação",
        help_text="Data da criação do ticket"
    )

    # Gerada ao encerrar um ticket
    data_encerramento = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Data de encerramento",
        help_text="Data de encerramento do ticket"
    )

    # Gerada automaticamente ao receber um novo comentário
    data_ultima_atualizacao = models.DateTimeField(
        null=False,
        auto_now=True,
        verbose_name="Data da última atualização do ticket",
        help_text="Data da última atualização do ticket"
    )

    # CATEGORIA DO TICKET
    # Definido pelo usuário

    class EscolhaCategoria(models.TextChoices):
        HARDWARE = 'HW', "Hardware",
        SOFTWARE = 'SW', "Software",
        REDES = 'RD', "Redes"

    categoria = models.CharField(
        choices=EscolhaCategoria.choices,
        max_length=2,
        null=False,
        default=EscolhaCategoria.HARDWARE,
        help_text='Escolha a categoria do seu ticket',
        verbose_name='Categoria'
    )

    # PRIORIDADE DO TICKET
    # Definido pelo usuário

    class EscolhaPrioridade(models.TextChoices):
        ALTA = 'P1', 'Alta',
        MODERADA = 'P2', 'Moderada',
        BAIXA = 'P3', 'Baixa'

    prioridade = models.CharField(
        max_length=2,
        null=False,
        choices=EscolhaPrioridade.choices,
        default=EscolhaPrioridade.BAIXA,
        help_text="Escolha a prioridade do ticket",
        verbose_name="Prioridade"
    )

    # ESTADO DO TICKET
    # Ao criar o ticket a primeira vez, será Aberto
    # Quando um técnico encerrar o ticket, será Encerrado
    # Quando um usuário/técnico cancelar o ticket, será Cancelado

    class EscolhaEstado(models.TextChoices):
        ABERTO = 'AB', 'Aberto',
        ENCERRADO = 'EN', 'Encerrado',
        CANCELADO = 'CC', 'Cancelado',
        EM_ANDAMENTO = 'EA', 'Em Andamento',
        EM_ESPERA = 'EE', 'Em Espera'

    estado = models.CharField(
        max_length=2,
        null=False,
        choices=EscolhaEstado.choices,
        default=EscolhaEstado.ABERTO,
        help_text="Estado atual do ticket",
        verbose_name="Estado"
    )

    # INFORMAÇÕES DESCRITIVAS DO TICKET

    # Título do ticket
    titulo = models.CharField(
        max_length=50,
        null=False,
        help_text="Insira o titulo do ticket",
        verbose_name="Título"
    )

    # Descrição do ticket
    descricao = models.TextField(
        null=False,
        help_text="Descreva em detalhes a sua solicitação",
        verbose_name="Descrição"
    )

    # Solução do ticket
    # PREENCHIDA SOMENTE NO ENCERRAMENTO
    solucao = models.TextField(
        null=True,
        blank=True,
        default='',
        help_text="Descreva em detalhes a solução deste ticket",
        verbose_name="Solução"
    )

    # Técnico associado ao ticket
    tecnico = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        verbose_name="Técnico",
        related_name="tecnico"
    )

    # Registro do criador do ticket
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        verbose_name="Solicitante",
        related_name="solicitante"
    )

    motivo_cancelamento = models.TextField(
        null=True,
        blank=True,
        default='',
        help_text="Descreva em detalhes o motivo do cancelamento deste ticket",
        verbose_name="Motivo do cancelamento"
    )

    def get_absolute_url(self):
        return reverse('ticket_detalhe', args=[str(self.id)])

    def __str__(self):
        return f'{self.id} - {self.titulo} - {self.estado}'

    def save(self, *args, **kwargs):
        # Lista de estados que NÃO devem possuir solução, motivo de cancelamento ou data de encerramento
        estados_ativos = [
            self.EscolhaEstado.ABERTO,       # Ajuste a constante conforme o seu TextChoices
            self.EscolhaEstado.EM_ANDAMENTO, # Ajuste conforme o seu TextChoices
            self.EscolhaEstado.EM_ESPERA     # Ajuste conforme o seu TextChoices
        ]

        # Se o estado atual for Aberto, Em Andamento ou Em Espera, limpa os campos de encerramento/cancelamento
        if self.estado in estados_ativos:
            if self.estado == self.EscolhaEstado.ABERTO:
                if self.tecnico: self.tecnico = None

            self.solucao = None
            self.motivo_cancelamento = None
            self.data_encerramento = None
            
        elif self.estado == self.EscolhaEstado.ENCERRADO:
            # Limpa o motivo de cancelamento caso exista pois não é relevante
            if self.motivo_cancelamento: self.motivo_cancelamento = None
            
            # Preenche automaticamento a data_encerramento caso ela esteja vazia:
            if not self.data_encerramento:
                self.data_encerramento = timezone.now()
        elif self.estado == self.EscolhaEstado.CANCELADO:
            # Limpa a solução caso exista pois não é relevante
            if self.solucao: self.solucao = None

            # Gera a data de encerramento automaticamente
            if not self.data_encerramento:
                self.data_encerramento = timezone.now()

        # Chama o save original do Django para persistir as alterações
        super().save(*args, **kwargs)

    class Meta:
        permissions = (
            ("pode_encerrar", "Pode encerrar o ticket"),
            ("pode_cancelar", "Pode cancelar o ticket"),
        )

class Comentario(models.Model):
    '''
    Modelo usado para representar comentários de um ticket.\n
    id -> BigAutoField, chave primária\n
    ticket -> ForeignKey, modelo "Ticket"\n
    comentario -> TextField\n
    data_comentario -> datetime\n
    usuario -> ForeignKey, modelo "Usuario"\n
    '''
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.RESTRICT,
        verbose_name="ID do ticket"
    )

    data = models.DateTimeField(
        auto_now_add=True,
        null=False,
        verbose_name="Data do comentário"
    )

    comentario = models.TextField(
        null=False,
        verbose_name="Comentário"
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        verbose_name="Usuário"
    )

    def __str__(self):
        return f'{self.data} - {self.usuario} - {self.comentario}'

class Historico(models.Model):
    '''
    Modelo usado para registrar um histórico de ações nos tickets.\n
    ticket -> ForeignKey, modelo "Ticket"\n
    usuario -> ForeignKey, modelo "User"\n
    tipo -> CharField (CRIACAO, ATUALIZACAO, MUDANCA_STATUS, COMENTARIO)\n
    acao -> TextField\n
    data -> datetime\n
    '''

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        verbose_name='Ticket'
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário'
    )

    class TipoAcao(models.TextChoices):
        CRIACAO = 'CRIACAO', 'Criação de ticket',
        ENCERRAMENTO = 'ENCERRAMENTO', 'Encerramento de ticket',
        CANCELAMENTO = 'CANCELAMENTO', 'Cancelamento de ticket',
        TECNICO = 'TECNICO', 'Mudança de técnico',
        ESTADO = 'ESTADO', 'Mudança de estado',
        PRIORIDADE = 'PRIORIDADE', 'Mudança de prioridade',
        COMENTARIO = 'COMENTARIO', 'Comentário'

        
    tipo = models.CharField(
        choices=TipoAcao.choices, 
        default=TipoAcao.ESTADO,
        max_length=12,
        verbose_name='Tipo de ação'
    )

    acao = models.TextField(verbose_name='Descrição da ação')

    data = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data e hora'
    )

    def __str__(self):
        return f"[{self.data.strftime('%d/%m/%Y %H:%M')}] Ticket #{self.ticket.id} - {self.acao[:30]} - {self.usuario}"

    def save(self, *args, **kwargs):
        usuario = self.usuario.get_username() if self.usuario else "Sistema"

        acoes = {
            self.TipoAcao.CRIACAO: f"Ticket criado por {usuario}",
            self.TipoAcao.ENCERRAMENTO: f"Ticket encerrado por {usuario}",
            self.TipoAcao.CANCELAMENTO: f"Ticket cancelado por {usuario}",
            self.TipoAcao.TECNICO: f"Técnico foi alocado/desalocado do ticket por {usuario}",
            self.TipoAcao.ESTADO: f"Estado do ticket alterado por {usuario}",
            self.TipoAcao.PRIORIDADE: f"Prioridade alterada por {usuario}",
            self.TipoAcao.COMENTARIO: f"Comentário adicionado por {usuario}",
        }

        self.acao = acoes.get(self.tipo, f"Ação realizada por {usuario}")

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Histórico do Ticket"
        verbose_name_plural = "Históricos dos Tickets"
        ordering = ['-data'] # Garante que os logs mais recentes apareçam primeiro por padrão