from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.forms import ModelForm, Textarea, TextInput, Select

INPUT_CLASSES = (
    "block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm "
    "text-slate-900 placeholder:text-slate-400 shadow-sm transition "
    "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 "
    "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500"
)

SELECT_CLASSES = (
    "block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm "
    "text-slate-900 shadow-sm transition "
    "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
)

TEXTAREA_CLASSES = INPUT_CLASSES + " min-h-32 resize-y leading-relaxed"

class TailwindFormMixin:
    """Aplica as classes Tailwind a todos os widgets de um ModelForm.

    Seleciona a classe adequada conforme o tipo de widget para que inputs,
    selects e textareas fiquem consistentes sem precisar declarar `widgets`
    manualmente em cada Meta.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, Textarea):
                css = TEXTAREA_CLASSES
            elif isinstance(widget, Select):
                css = SELECT_CLASSES
            else:
                css = INPUT_CLASSES
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css}".strip()

class LoginForm(TailwindFormMixin, AuthenticationForm):
    """Formulário de autenticação com widgets estilizados no padrão PyDesk.

    Herda de AuthenticationForm (usado pela LoginView do Django) e aplica as
    mesmas classes Tailwind dos demais formulários via TailwindFormMixin.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Usuário", "autofocus": True, "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Senha", "autocomplete": "current-password"}
        )

class RecuperarSenhaForm(TailwindFormMixin, PasswordResetForm):
    """Solicitação de redefinição de senha (usado pela PasswordResetView).

    Estiliza o campo de email no padrão PyDesk. É consumido pelo template
    `password_reset_form.html`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "voce@empresa.com",
                "autocomplete": "email",
                "autofocus": True,
            }
        )

class DefinirSenhaForm(TailwindFormMixin, SetPasswordForm):
    """Definição da nova senha (usado pela PasswordResetConfirmView).

    Estiliza os campos `new_password1`/`new_password2` e alimenta o template
    `password_reset_confirm.html` com os textos de ajuda e erros de validação.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(
            {"placeholder": "Nova senha", "autocomplete": "new-password"}
        )
        self.fields["new_password2"].widget.attrs.update(
            {"placeholder": "Confirme a nova senha", "autocomplete": "new-password"}
        )