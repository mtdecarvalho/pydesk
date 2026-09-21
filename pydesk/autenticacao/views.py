from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy

from .forms import LoginForm, RecuperarSenhaForm, DefinirSenhaForm


class PyDeskLoginView(LoginView):
    """View de login do PyDesk.

    Reaproveita a LoginView do Django (que já cuida do fluxo de autenticação,
    do parâmetro `next` e do redirecionamento) e apenas troca o template e o
    formulário pelos do PyDesk.
    """

    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class PyDeskPasswordResetView(PasswordResetView):
    """Solicitação de redefinição de senha (etapa 1).

    Renderiza o formulário de email e dispara o email de redefinição. O corpo
    do email usa o template HTML do PyDesk; o assunto continua no template
    padrão do Django (`registration/password_reset_subject.txt`).
    """

    template_name = "password_reset_form.html"
    form_class = RecuperarSenhaForm
    email_template_name = "password_reset_email.html"
    html_email_template_name = "password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class PyDeskPasswordResetDoneView(PasswordResetDoneView):
    """Confirmação de envio do email (etapa 2)."""

    template_name = "password_reset_done.html"


class PyDeskPasswordResetConfirmView(PasswordResetConfirmView):
    """Definição da nova senha a partir do link do email (etapa 3)."""

    template_name = "password_reset_confirm.html"
    form_class = DefinirSenhaForm
    success_url = reverse_lazy("password_reset_complete")


class PyDeskPasswordResetCompleteView(PasswordResetCompleteView):
    """Confirmação de que a senha foi alterada com sucesso (etapa 4)."""

    template_name = "password_reset_complete.html"
