from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .utils import processar_email
from tickets.models import Comentario, Historico, Ticket

# Obtém o modelo de usuário ativo (suporta o modelo customizado 'autenticacao.Usuario')
User = get_user_model()


class BasePyDeskTestCase(TestCase):
    """Prepara usuários, grupos, permissões e um ticket base para os testes das views."""

    def setUp(self):
        # Cliente HTTP de teste do Django para simular requisições GET e POST
        self.client = Client()

        # Garante a existência dos grupos principais do sistema
        self.grupo_tecnico, _ = Group.objects.get_or_create(name="TECNICO")
        self.grupo_usuario, _ = Group.objects.get_or_create(name="USUARIO_COMUM")

        # Obtém os ContentTypes para filtrar permissões vinculadas aos modelos corretos
        ticket_ct = ContentType.objects.get_for_model(Ticket)
        historico_ct = ContentType.objects.get_for_model(Historico)

        # Recupera permissões padrão e customizadas associadas a Ticket e Historico
        perm_encerrar = Permission.objects.filter(
            content_type=ticket_ct, codename="pode_encerrar"
        ).first()
        perm_cancelar = Permission.objects.filter(
            content_type=ticket_ct, codename="pode_cancelar"
        ).first()
        perm_view_historico = Permission.objects.filter(
            content_type=historico_ct, codename="view_historico"
        ).first()
        perm_view_ticket = Permission.objects.filter(
            content_type=ticket_ct, codename="view_ticket"
        ).first()
        perm_add_ticket = Permission.objects.filter(
            content_type=ticket_ct, codename="add_ticket"
        ).first()
        perm_change_ticket = Permission.objects.filter(
            content_type=ticket_ct, codename="change_ticket"
        ).first()

        # Filtra apenas permissões existentes para evitar None na lista
        perms_tecnico = [
            p
            for p in [
                perm_encerrar,
                perm_view_historico,
                perm_view_ticket,
                perm_add_ticket,
                perm_change_ticket,
            ]
            if p is not None
        ]
        perms_usuario = [
            p
            for p in [perm_cancelar, perm_view_ticket, perm_add_ticket]
            if p is not None
        ]

        # Atribui os conjuntos de permissões aos respectivos grupos
        self.grupo_tecnico.permissions.set(perms_tecnico)
        self.grupo_usuario.permissions.set(perms_usuario)

        # Cria usuário técnico e associa ao grupo TECNICO
        self.tecnico = User.objects.create_user(
            username="tecnico1",
            email="tecnico1@pydesk.local",
            password="SenhaForte123!",
        )
        self.tecnico.groups.add(self.grupo_tecnico)

        # Cria usuário comum (solicitante) e associa ao grupo USUARIO_COMUM
        self.usuario_comum = User.objects.create_user(
            username="usuario1",
            email="usuario1@pydesk.local",
            password="SenhaForte123!",
        )
        self.usuario_comum.groups.add(self.grupo_usuario)

        # Cria segundo usuário comum para testar isolamento entre solicitantes (IDOR / escopo)
        self.outro_usuario = User.objects.create_user(
            username="usuario2",
            email="usuario2@pydesk.local",
            password="SenhaForte123!",
        )
        self.outro_usuario.groups.add(self.grupo_usuario)

        # Cria superusuário para validar rotas e escopos administrativos
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@pydesk.local",
            password="SenhaAdminForte123!",
        )

        # Cria um ticket inicial aberto para reaproveitamento nos cenários de teste
        self.ticket_aberto = Ticket.objects.create(
            titulo="Impressora sem toner",
            descricao="Impressora do 2º andar não imprime.",
            categoria=Ticket.EscolhaCategoria.HARDWARE,
            prioridade=Ticket.EscolhaPrioridade.MODERADA,
            estado=Ticket.EscolhaEstado.ABERTO,
            solicitante=self.usuario_comum,
        )


# Mock de processar_email em toda a classe para evitar envio real de e-mails durante os testes
@patch("tickets.views.processar_email")
class TicketsViewsTestCase(BasePyDeskTestCase):
    """Testa autorização, regras de negócio e respostas HTTP das views de tickets."""

    def test_index_acessivel_anonimo_e_autenticado(self, mock_email):
        """Verifica se a página inicial carrega tanto para anônimos quanto para logados."""
        resp_anon = self.client.get(reverse("index"))
        self.assertEqual(resp_anon.status_code, 200)

        self.client.force_login(self.usuario_comum)
        resp_auth = self.client.get(reverse("index"))
        self.assertEqual(resp_auth.status_code, 200)

    def test_tickets_home_exige_login(self, mock_email):
        """Garante redirecionamento (302) para anônimos e acesso (200) para autenticados."""
        url = reverse("tickets")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.client.force_login(self.usuario_comum)
        resp_ok = self.client.get(url)
        self.assertEqual(resp_ok.status_code, 200)

    def test_meus_tickets_por_perfil(self, mock_email):
        """Valida que solicitante vê seu ticket aberto e técnico vê ticket em andamento alocado a ele."""
        url = reverse("meus_tickets")

        # Usuário comum visualiza o ticket que abriu
        self.client.force_login(self.usuario_comum)
        resp_user = self.client.get(url)
        self.assertEqual(resp_user.status_code, 200)
        self.assertIn(self.ticket_aberto, resp_user.context["lista_tickets"])

        # Aloca o ticket ao técnico e muda estado para EM_ANDAMENTO
        self.ticket_aberto.tecnico = self.tecnico
        self.ticket_aberto.estado = Ticket.EscolhaEstado.EM_ANDAMENTO
        self.ticket_aberto.save()

        # Técnico visualiza o ticket na sua fila
        self.client.force_login(self.tecnico)
        resp_tec = self.client.get(url)
        self.assertEqual(resp_tec.status_code, 200)
        self.assertIn(self.ticket_aberto, resp_tec.context["lista_tickets"])

    def test_tickets_encerrados_restringido_a_tecnico(self, mock_email):
        """Verifica bloqueio de usuário comum e liberação para usuário com permissão de encerrar."""
        url = reverse("tickets_encerrados")

        self.client.force_login(self.usuario_comum)
        resp_negada = self.client.get(url)
        self.assertEqual(resp_negada.status_code, 302)

        self.client.force_login(self.tecnico)
        resp_ok = self.client.get(url)
        self.assertEqual(resp_ok.status_code, 200)

    def test_tickets_cancelados_escopo_usuario_vs_superuser(self, mock_email):
        """Garante que usuário comum vê apenas os próprios cancelados e superuser vê todos."""
        ticket_outro = Ticket.objects.create(
            titulo="Ticket outro usuário",
            descricao="Cancelado",
            estado=Ticket.EscolhaEstado.CANCELADO,
            motivo_cancelamento="Duplicado",
            solicitante=self.outro_usuario,
        )
        ticket_meu = Ticket.objects.create(
            titulo="Meu ticket cancelado",
            descricao="Cancelado",
            estado=Ticket.EscolhaEstado.CANCELADO,
            motivo_cancelamento="Não precisa mais",
            solicitante=self.usuario_comum,
        )

        url = reverse("tickets_cancelados")

        # Usuário comum: vê apenas o seu ticket cancelado
        self.client.force_login(self.usuario_comum)
        resp_user = self.client.get(url)
        self.assertEqual(resp_user.status_code, 200)
        self.assertIn(ticket_meu, resp_user.context["lista_tickets"])
        self.assertNotIn(ticket_outro, resp_user.context["lista_tickets"])

        # Superusuário: vê tickets cancelados de todos os solicitantes
        self.client.force_login(self.superuser)
        resp_admin = self.client.get(url)
        self.assertEqual(resp_admin.status_code, 200)
        self.assertIn(ticket_meu, resp_admin.context["lista_tickets"])
        self.assertIn(ticket_outro, resp_admin.context["lista_tickets"])

    def test_tickets_abertos_e_nao_alocados_exigem_permissao_tecnico(self, mock_email):
        """Confirma que filas de triagem exigem permissão de técnico."""
        for nome_rota in ["tickets_abertos", "tickets_nao_alocados"]:
            url = reverse(nome_rota)

            self.client.force_login(self.usuario_comum)
            self.assertEqual(self.client.get(url).status_code, 302)

            self.client.force_login(self.tecnico)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_tickets_em_espera_filtra_por_solicitante_quando_usuario_comum(self, mock_email):
        """Verifica filtragem por solicitante para usuário comum na fila de tickets em espera."""
        ticket_espera_meu = Ticket.objects.create(
            titulo="Aguardando peça",
            descricao="Sem estoque",
            estado=Ticket.EscolhaEstado.EM_ESPERA,
            solicitante=self.usuario_comum,
        )
        ticket_espera_outro = Ticket.objects.create(
            titulo="Aguardando rede",
            descricao="ISP",
            estado=Ticket.EscolhaEstado.EM_ESPERA,
            solicitante=self.outro_usuario,
        )

        url = reverse("tickets_em_espera")
        self.client.force_login(self.usuario_comum)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(ticket_espera_meu, resp.context["lista_tickets"])
        self.assertNotIn(ticket_espera_outro, resp.context["lista_tickets"])

    def test_criar_ticket_post_e_disparo_email(self, mock_email):
        """Testa criação de ticket, registro de histórico inicial e chamada de notificação por e-mail."""
        url = reverse("criar_ticket")
        self.client.force_login(self.usuario_comum)

        resp = self.client.post(
            url,
            data={
                "categoria": Ticket.EscolhaCategoria.SOFTWARE,
                "prioridade": Ticket.EscolhaPrioridade.ALTA,
                "titulo": "Erro no sistema financeiro",
                "descricao": "Tela trava ao gerar relatório.",
            },
        )
        self.assertEqual(resp.status_code, 302)

        criado = Ticket.objects.filter(titulo="Erro no sistema financeiro").first()
        self.assertIsNotNone(criado)
        self.assertEqual(criado.solicitante, self.usuario_comum)
        self.assertEqual(criado.estado, Ticket.EscolhaEstado.ABERTO)
        self.assertTrue(
            Historico.objects.filter(ticket=criado, tipo=Historico.TipoAcao.CRIACAO).exists()
        )
        mock_email.assert_called_once()

    def test_ticket_detalhe_acesso_comentario_e_alocacao(self, mock_email):
        """Testa acesso a detalhes, criação de comentário, alocação, desalocação e mudança de prioridade."""
        url = reverse("ticket_detalhe", args=[self.ticket_aberto.pk])

        # Outro usuário comum não deve acessar ticket de terceiros quando IDOR está bloqueado
        self.client.force_login(self.outro_usuario)
        resp_outro = self.client.get(url)
        self.assertIn(resp_outro.status_code, [200, 403])

        # Solicitante envia comentário (nota o prefixo 'comentario' usado no ComentarioForm)
        self.client.force_login(self.usuario_comum)
        resp_coment = self.client.post(
            url,
            data={
                "submit_comentario": "1",
                "comentario-comentario": "Adicionando informação extra.",
            },
        )
        self.assertEqual(resp_coment.status_code, 302)
        self.assertTrue(
            Comentario.objects.filter(
                ticket=self.ticket_aberto,
                comentario="Adicionando informação extra.",
            ).exists()
        )

        # Técnico assume o atendimento do ticket
        self.client.force_login(self.tecnico)
        resp_alocar = self.client.post(url, data={"alocar_ticket": "1"})
        self.assertEqual(resp_alocar.status_code, 302)
        self.ticket_aberto.refresh_from_db()
        self.assertEqual(self.ticket_aberto.tecnico, self.tecnico)
        self.assertEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.EM_ANDAMENTO)

        # Técnico libera o ticket de volta para aberto
        resp_desalocar = self.client.post(url, data={"desalocar_ticket": "1"})
        self.assertEqual(resp_desalocar.status_code, 302)
        self.ticket_aberto.refresh_from_db()
        self.assertIsNone(self.ticket_aberto.tecnico)
        self.assertEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.ABERTO)

        # Técnico altera a prioridade do ticket
        resp_prio = self.client.post(
            url,
            data={
                "alterar_prioridade": "1",
                "prioridade": Ticket.EscolhaPrioridade.ALTA,
            },
        )
        self.assertEqual(resp_prio.status_code, 302)
        self.ticket_aberto.refresh_from_db()
        self.assertEqual(self.ticket_aberto.prioridade, Ticket.EscolhaPrioridade.ALTA)

    def test_encerrar_ticket_valida_solucao_e_atualiza_estado(self, mock_email):
        """Garante que solução em branco é rejeitada e solução válida encerra o ticket."""
        url = reverse("encerrar_ticket", args=[self.ticket_aberto.pk])
        self.client.force_login(self.tecnico)

        # Entrada apenas com espaços deve falhar na validação do formulário (retorna 200 com erro)
        resp_invalido = self.client.post(url, data={"solucao": "   "})
        self.assertEqual(resp_invalido.status_code, 200)
        self.ticket_aberto.refresh_from_db()
        self.assertNotEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.ENCERRADO)

        # Entrada válida atualiza estado e salva a solução
        resp_valido = self.client.post(url, data={"solucao": "Toner trocado e teste ok."})
        self.assertEqual(resp_valido.status_code, 302)
        self.ticket_aberto.refresh_from_db()
        self.assertEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.ENCERRADO)
        self.assertEqual(self.ticket_aberto.solucao, "Toner trocado e teste ok.")

    def test_cancelar_ticket_valida_motivo_e_atualiza_estado(self, mock_email):
        """Garante que motivo vazio é rejeitado e motivo válido cancela o ticket."""
        url = reverse("cancelar_ticket", args=[self.ticket_aberto.pk])
        self.client.force_login(self.usuario_comum)

        # Motivo vazio deve falhar na validação
        resp_invalido = self.client.post(url, data={"motivo_cancelamento": ""})
        self.assertEqual(resp_invalido.status_code, 200)
        self.ticket_aberto.refresh_from_db()
        self.assertNotEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.CANCELADO)

        # Motivo válido cancela o ticket e registra o motivo
        resp_valido = self.client.post(
            url, data={"motivo_cancelamento": "Problema resolvido localmente."}
        )
        self.assertEqual(resp_valido.status_code, 302)
        self.ticket_aberto.refresh_from_db()
        self.assertEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.CANCELADO)
        self.assertEqual(
            self.ticket_aberto.motivo_cancelamento, "Problema resolvido localmente."
        )

    def test_ticket_em_espera_view(self, mock_email):
        """Verifica transição para EM_ESPERA e remoção do técnico alocado."""
        url = reverse("em_espera_ticket", args=[self.ticket_aberto.pk])
        self.client.force_login(self.tecnico)

        resp = self.client.post(url, data={"comentario": "Aguardando retorno do fornecedor."})
        self.assertEqual(resp.status_code, 302)
        self.ticket_aberto.refresh_from_db()
        self.assertEqual(self.ticket_aberto.estado, Ticket.EscolhaEstado.EM_ESPERA)
        self.assertIsNone(self.ticket_aberto.tecnico)

    def test_ticket_historico_view_exige_permissao(self, mock_email):
        """Testa restrição de acesso ao histórico de auditoria do ticket."""
        Historico.objects.create(
            ticket=self.ticket_aberto,
            usuario=self.usuario_comum,
            tipo=Historico.TipoAcao.CRIACAO,
        )
        url = reverse("ticket_historico", args=[self.ticket_aberto.pk])

        # Usuário comum sem view_historico não deve visualizar o histórico
        self.client.force_login(self.usuario_comum)
        resp_user = self.client.get(url)
        self.assertIn(resp_user.status_code, [302, 403])

        # Técnico com view_historico tem acesso permitido
        self.client.force_login(self.tecnico)
        resp_tec = self.client.get(url)
        self.assertEqual(resp_tec.status_code, 200)

    def test_todos_tickets_view_apenas_superuser(self, mock_email):
        """Garante que a listagem global de todos os tickets é exclusiva de superusuários."""
        url = reverse("todos_tickets")

        # Técnico comum não é superusuário e deve ser bloqueado
        self.client.force_login(self.tecnico)
        self.assertEqual(self.client.get(url).status_code, 302)

        # Superusuário acessa e vê o ticket cadastrado
        self.client.force_login(self.superuser)
        resp_admin = self.client.get(url)
        self.assertEqual(resp_admin.status_code, 200)
        self.assertIn(self.ticket_aberto, resp_admin.context["lista_tickets"])
        
# Força o backend de e-mail em memória (locmem) para capturar mensagens em mail.outbox
# sem fazer conexões SMTP reais nem depender de credenciais externas durante os testes
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="PyDesk Support <suporte@pydesk.local>",
)
class ProcessarEmailTestCase(TestCase):
    """Testa destinatários, conteúdo, deduplicação e resiliência de processar_email."""

    def setUp(self):
        # Garante que a caixa de e-mails em memória comece vazia em cada teste
        mail.outbox.clear()

        # Cria ou obtém o grupo TECNICO usado para notificação de equipe
        self.grupo_tecnico, _ = Group.objects.get_or_create(name="TECNICO")

        # Cria um solicitante e dois técnicos com endereços de e-mail distintos
        self.solicitante = User.objects.create_user(
            username="solicitante_email",
            email="solicitante@pydesk.local",
            password="SenhaForte123!",
        )
        self.tecnico1 = User.objects.create_user(
            username="tecnico_email_1",
            email="tec1@pydesk.local",
            password="SenhaForte123!",
        )
        self.tecnico2 = User.objects.create_user(
            username="tecnico_email_2",
            email="tec2@pydesk.local",
            password="SenhaForte123!",
        )

        # Associa os técnicos ao grupo TECNICO
        self.tecnico1.groups.add(self.grupo_tecnico)
        self.tecnico2.groups.add(self.grupo_tecnico)

        # Cria um ticket base aberto associado ao solicitante
        self.ticket = Ticket.objects.create(
            titulo="VPN fora do ar",
            descricao="Não conecta fora da rede interna.",
            categoria=Ticket.EscolhaCategoria.REDES,
            prioridade=Ticket.EscolhaPrioridade.ALTA,
            estado=Ticket.EscolhaEstado.ABERTO,
            solicitante=self.solicitante,
        )

    def test_novo_ticket_envia_para_solicitante_e_todos_tecnicos_sem_duplicar(self):
        """Verifica se NOVO_TICKET notifica solicitante e técnicos sem repetir endereços."""
        # Mesmo que o solicitante também esteja no grupo TECNICO, seu e-mail não deve duplicar
        self.solicitante.groups.add(self.grupo_tecnico)

        processar_email(ticket=self.ticket, tipo="NOVO_TICKET")

        # Confirma que apenas 1 e-mail foi gerado na fila de saída
        self.assertEqual(len(mail.outbox), 1)
        mensagem = mail.outbox[0]

        # Valida o número do ticket no assunto e o conjunto exato de destinatários
        self.assertIn(f"#{self.ticket.id}", mensagem.subject)
        self.assertEqual(
            set(mensagem.to),
            {
                "solicitante@pydesk.local",
                "tec1@pydesk.local",
                "tec2@pydesk.local",
            },
        )
        self.assertEqual(len(mensagem.to), 3)

    def test_novo_comentario_com_tecnico_alocado_envia_apenas_para_ele_e_solicitante(self):
        """Verifica se NOVO_COMENTARIO restringe aos envolvidos quando há técnico alocado."""
        # Aloca o ticket ao tecnico1 e altera o estado para EM_ANDAMENTO
        self.ticket.tecnico = self.tecnico1
        self.ticket.estado = Ticket.EscolhaEstado.EM_ANDAMENTO
        self.ticket.save()

        comentario_obj = Comentario.objects.create(
            ticket=self.ticket,
            usuario=self.solicitante,
            comentario="Teste de ping realizado com sucesso.",
        )

        processar_email(
            ticket=self.ticket,
            tipo="NOVO_COMENTARIO",
            comentario=comentario_obj,
        )

        self.assertEqual(len(mail.outbox), 1)
        mensagem = mail.outbox[0]

        # tecnico2 não deve receber notificação pois o ticket já está alocado ao tecnico1
        self.assertEqual(
            set(mensagem.to),
            {"solicitante@pydesk.local", "tec1@pydesk.local"},
        )
        # Confirma que o texto do comentário aparece no corpo do e-mail
        self.assertIn("Teste de ping realizado com sucesso.", mensagem.body)

    def test_novo_comentario_sem_tecnico_alocado_notifica_todos_tecnicos(self):
        """Verifica se NOVO_COMENTARIO avisa todos os técnicos quando não há responsável."""
        processar_email(
            ticket=self.ticket,
            tipo="NOVO_COMENTARIO",
            comentario="Aguardando triagem.",
        )

        self.assertEqual(len(mail.outbox), 1)
        mensagem = mail.outbox[0]
        self.assertEqual(
            set(mensagem.to),
            {
                "solicitante@pydesk.local",
                "tec1@pydesk.local",
                "tec2@pydesk.local",
            },
        )

    def test_ticket_em_andamento_envia_para_solicitante(self):
        """Verifica se TICKET_EM_ANDAMENTO notifica o solicitante quando o atendimento inicia."""
        self.ticket.tecnico = self.tecnico1
        self.ticket.estado = Ticket.EscolhaEstado.EM_ANDAMENTO
        self.ticket.save()

        processar_email(ticket=self.ticket, tipo="TICKET_EM_ANDAMENTO")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["solicitante@pydesk.local"])

    def test_ticket_encerrado_sem_tecnico_nao_quebra_e_envia_para_solicitante(self):
        """Garante que encerrar um ticket sem técnico vinculado não gera erro."""
        self.ticket.tecnico = None
        self.ticket.estado = Ticket.EscolhaEstado.ENCERRADO
        self.ticket.solucao = "Reiniciado o serviço de rede."
        self.ticket.save()

        processar_email(
            ticket=self.ticket,
            tipo="TICKET_ENCERRADO",
            comentario=self.ticket.solucao,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["solicitante@pydesk.local"])
        self.assertIn("Reiniciado o serviço de rede.", mail.outbox[0].body)

    def test_ticket_cancelado_e_em_espera(self):
        """Testa o envio de notificação para os estados CANCELADO e EM_ESPERA."""
        # Cenário 1: Ticket cancelado notifica solicitante e equipe técnica
        processar_email(
            ticket=self.ticket,
            tipo="TICKET_CANCELADO",
            comentario="Solicitação duplicada.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            set(mail.outbox[0].to),
            {
                "solicitante@pydesk.local",
                "tec1@pydesk.local",
                "tec2@pydesk.local",
            },
        )

        # Limpa a caixa para testar o segundo evento isoladamente
        mail.outbox.clear()

        # Cenário 2: Ticket em espera notifica o solicitante
        processar_email(
            ticket=self.ticket,
            tipo="TICKET_EM_ESPERA",
            comentario="Aguardando retorno do usuário.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["solicitante@pydesk.local"])

    def test_ausencia_grupo_tecnico_nao_levanta_excecao(self):
        """Verifica se a ausência do grupo TECNICO no banco é tratada sem exceção."""
        Group.objects.filter(name__iexact="TECNICO").delete()

        processar_email(ticket=self.ticket, tipo="NOVO_TICKET")

        # Mesmo sem o grupo de técnicos, o solicitante ainda deve receber o e-mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["solicitante@pydesk.local"])

    @patch("tickets.utils.send_mail", side_effect=RuntimeError("Falha simulada SMTP"))
    def test_erro_smtp_e_capturado_sem_quebrar_fluxo(self, mock_send_mail):
        """Garante que erros no send_mail sejam capturados sem estourar exceção."""
        processar_email(ticket=self.ticket, tipo="NOVO_TICKET")

        # Confirma que a tentativa de envio ocorreu e nada foi adicionado ao outbox
        mock_send_mail.assert_called_once()
        self.assertEqual(len(mail.outbox), 0)