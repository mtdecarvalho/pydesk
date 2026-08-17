from datetime import datetime

from django.db import models
from pydesk.settings import AUTH_USER_MODEL as User
from django.contrib.auth.models import Group

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(
        max_length=10,
        null=False
    )

    equipe_padrao = models.ForeignKey(
        Group,
        on_delete=models.RESTRICT,
        null=False
    )

    def __str__(self):
        return self.nome

class Ticket(models.Model):
    '''Modelo usado para representar um ticket.'''
    id = models.BigAutoField(primary_key=True)

    # DATAS USADAS NO TICKET

    # Gerada automaticamente na abertura
    data_abertura = models.DateTimeField(
        auto_now_add=True,
        null=False,
        verbose_name="Data de abertura do ticket",
        help_text="Data de abertura do ticket"
    )

    # Gerada ao encerrar um ticket
    data_encerramento = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Data de encerramento do ticket",
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
    # O usuário seleciona isso e a aplicação direciona para a equipe correta
    # Definido pelo usuário
    categoria = models.ForeignKey(
        Categoria,
        null=False,
        on_delete=models.RESTRICT
    )

    # Fila da equipe atualmente responsável pelo ticket, preenchido automaticamente pelo sistema
    # Atribuido automaticamente pelo sistema na criação do chamado
    equipe = models.ForeignKey(
        Group,
        on_delete=models.RESTRICT,
        related_name="fila_equipe"
    )

    # configuration_item =

    # PRIORIDADE DO TICKET

    ALTA = "P1"
    MODERADA = "P2"
    BAIXA = "P3"

    ESCOLHA_PRIORIDADE = (
        (ALTA, 'Alta'),
        (MODERADA, 'Moderada'),
        (BAIXA, 'Baixa')
    )

    prioridade = models.CharField(
        max_length=2,
        null=False,
        choices=ESCOLHA_PRIORIDADE,
        default=BAIXA,
        help_text="Escolha a prioridade do ticket",
        verbose_name="Prioridade do ticket"
    )

    # ESTADO DO TICKET
    # Ao criar o ticket a primeira vez, será Aberto
    # Quando um técnico puxar o ticket para sua fila, será Em Atendimento
    # Quando um técnico encerrar o ticket, será Solucionado
    # Quando um usuário/técnico cancelar o ticket, será Cancelado
    # Na maioria das vezes, o estado vai ser alocado automaticamente pela aplicação

    ABERTO = "AB"
    EM_ATENDIMENTO = "EA"
    SOLUCIONADO = "SC"
    CANCELADO = "CC"

    ESCOLHA_ESTADO = (
        (ABERTO, "Aberto"),
        (EM_ATENDIMENTO, "Em Atendimento"),
        (SOLUCIONADO, "Solucionado"),
        (CANCELADO, "Cancelado")
    )

    estado = models.CharField(
        max_length=2,
        null=False,
        choices=ESCOLHA_ESTADO,
        default=ABERTO,
        help_text="Estado atual do ticket",
        verbose_name="Estado atual do ticket"
    )

    # INFORMAÇÕES DESCRITIVAS DO TICKET

    titulo = models.CharField(
        max_length=50,
        null=False,
        help_text="Insira o titulo do ticket",
        verbose_name="Título do ticket"
    )

    descricao = models.TextField(
        null=False,
        help_text="Descreva em detalhes o suporte que você precisa neste ticket",
        verbose_name="Descrição do ticket"
    )

    # PREENCHIDA SOMENTE NO ENCERRAMENTO

    solucao = models.TextField(
        null=True,
        blank=True,
        help_text="Descreva em detalhes o que foi feito para solucionar este ticket",
        verbose_name="Solução do ticket"
    )

    # Técnico associado ao ticket
    tecnico = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="tecnico"
    )

    # Solicitante (criador) do ticket
    # Vai ser atribuido automaticamente pela view
    solicitante = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="solicitante"
    )

    def save(self, **kwargs):
        # No primeiro salvamento, define a equipe associada ao ticket com base
        # na equipe padrão do modelo de Categoria
        # A pk só é gerada ao rodar o save(), então checando se ela existe ou não
        # é uma maneira de checar se o objeto já existe ou não
        if not self.pk and not self.equipe and self.categoria:
            self.equipe = self.categoria.equipe_padrao
            self.estado = self.ABERTO

        # ## Se houver um técnico associado, muda o estado para EM ATENDIMENTO
        # if self.tecnico:
        #     self.estado = self.EM_ATENDIMENTO
        # ## Se não houver técnico associado e o ticket não estiver encerrado, muda para ABERTO
        # elif not self.tecnico and not self.solucao and not self.data_encerramento:
        #     self.estado = self.ABERTO
# 
        # # Se a solução do ticket foi preenchida, muda o estado para SOLUCIONADO e gera a data de solução
        # if self.solucao:
        #     self.estado = self.SOLUCIONADO
        #     self.data_encerramento = datetime.now()
# 
        # # Se o ticket foi cancelado pelo solicitante, remove da lista do técnico responsável.
        # if self.estado == self.CANCELADO:
        #     self.tecnico = None

        # Roda o save() padrão do Django.
        super().save(**kwargs)

    def __str__(self):
        return f'${self.id} - ${self.titulo} - ${self.estado}'

class Comentario(models.Model):
    '''Modelo usado para representar comentários de um ticket.'''
    id = models.BigAutoField(primary_key=True)

    id_ticket = models.ForeignKey(
        Ticket,
        on_delete=models.RESTRICT,
        verbose_name="ID do ticket associado ao comentário"
    )

    comentario = models.TextField(
        null=False,
        help_text="Insira o texto do seu comentário",
        verbose_name="Comentário"
    )

    data_comentario = models.DateTimeField(
        auto_now_add=True,
        null=False,
        verbose_name="Data do comentário"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.RESTRICT
    )

    def __str__(self):
        return f'${self.data_comentario} - ${self.usuario} - ${self.comentario}'

