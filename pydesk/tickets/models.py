from datetime import datetime
import uuid

from django.db import models
from django.urls import reverse
from pydesk.settings import AUTH_USER_MODEL as Usuario

# Create your models here.

class Ativo(models.Model):
    '''
    Modelo usado para representar um ativo (hardware, software ou rede) da organização.
    id -> UUIDField, chave primária
    categoria -> CharField, choices = ESCOLHA_CATEGORIA
    nome -> CharField
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    HARDWARE = "HW"
    SOFTWARE = "SW"
    REDES = "RD"

    ESCOLHA_CATEGORIA = (
        (HARDWARE, "Hardware"),
        (SOFTWARE, "Software"),
        (REDES, "Redes"),
    )

    categoria = models.CharField(
        choices=ESCOLHA_CATEGORIA,
        max_length=2,
        null=False,
        help_text="Escolha a categoria do ativo a ser registrado"
    )

    nome = models.CharField(
        null=False,
        help_text="Escreva o nome do ativo a ser registrado"
    )

    def get_absolute_url(self):
        return reverse('ativo-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.id} - {self.categoria} - {self.nome}'

class Ticket(models.Model):
    '''
    Modelo usado para representar um ticket.
    id -> BigAutoField, chave primária
    data_criacao -> datetime
    data_encerramento -> datetime
    data_ultima_atualizacao -> datetime
    categoria -> CharField, choices = ESCOLHA_CATEGORIA
    ativo -> ForeignKey, modelo "Ativo"
    prioridade -> CharField, choices = ESCOLHA_PRIORIDADE
    estado -> CharField, choices = ESCOLHA_ESTADO
    titulo -> CharField
    descricao -> TextField
    solucao -> TextField
    tecnico -> ForeignKey, modelo "Usuario"
    '''
    id = models.BigAutoField(primary_key=True)

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

    HARDWARE = "HW"
    SOFTWARE = "SW"
    REDES = "RD"

    ESCOLHA_CATEGORIA = (
        (HARDWARE, "Hardware"),
        (SOFTWARE, "Software"),
        (REDES, "Redes"),
    )

    categoria = models.CharField(
        choices=ESCOLHA_CATEGORIA,
        max_length=2,
        null=False,
        default=HARDWARE,
        help_text='Escolha a categoria do seu ticket',
        verbose_name='Categoria'
    )

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        null=False,
        default=None,
        help_text="Escolha o ativo associado à essa solicitação"
    )

    # PRIORIDADE DO TICKET
    # Definido pelo usuário
    ALTA = "P1"
    MODERADA = "P2"
    BAIXA = "P3"

    ESCOLHA_PRIORIDADE = (
        (ALTA, "Alta"),
        (MODERADA, "Moderada"),
        (BAIXA, "Baixa")
    )

    prioridade = models.CharField(
        max_length=2,
        null=False,
        choices=ESCOLHA_PRIORIDADE,
        default=BAIXA,
        help_text="Escolha a prioridade do ticket",
        verbose_name="Prioridade"
    )

    # ESTADO DO TICKET
    # Ao criar o ticket a primeira vez, será Aberto
    # Quando um técnico encerrar o ticket, será Encerrado
    # Quando um usuário/técnico cancelar o ticket, será Cancelado

    ABERTO = "AB"
    ENCERRADO = "EN"
    CANCELADO = "CC"

    ESCOLHA_ESTADO = (
        (ABERTO, "Aberto"),
        (ENCERRADO, "Encerrado"),
        (CANCELADO, "Cancelado")
    )

    estado = models.CharField(
        max_length=2,
        null=False,
        choices=ESCOLHA_ESTADO,
        default=ABERTO,
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
        help_text="Descreva em detalhes o que foi feito para solucionar este ticket",
        verbose_name="Solução"
    )

    # Técnico associado ao ticket
    tecnico = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        verbose_name="Técnico"
    )

    def get_absolute_url(self):
        return reverse('ticket-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.id} - {self.titulo} - {self.estado}'

class Comentario(models.Model):
    '''
    Modelo usado para representar comentários de um ticket.
    id -> BigAutoField, chave primária
    id_ticket -> ForeignKey, modelo "Ticket"
    comentario -> TextField
    data_comentario -> datetime
    usuario -> ForeignKey, modelo "Usuario"
    '''
    id = models.BigAutoField(primary_key=True)

    id_ticket = models.ForeignKey(
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
        help_text="Insira o texto do seu comentário",
        verbose_name="Comentário"
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        null=False
    )

    def __str__(self):
        return f'{self.data} - {self.usuario} - {self.comentario}'

