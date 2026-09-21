from django.forms import ModelForm, Textarea, TextInput, Select

from .models import Comentario, Ticket

# Classes Tailwind reutilizadas pelos widgets dos formulários.
# Mantêm os campos alinhados à identidade visual do PyDesk (paleta brand/slate).
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


class ComentarioForm(TailwindFormMixin, ModelForm):
    class Meta:
        model = Comentario
        fields = ["comentario"]
        widgets = {
            "comentario": Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Escreva um comentário...",
                }
            ),
        }


class CriarTicketForm(TailwindFormMixin, ModelForm):
    class Meta:
        model = Ticket
        fields = ["categoria", "prioridade", "titulo", "descricao"]
        widgets = {
            "titulo": TextInput(
                attrs={"placeholder": "Resumo objetivo do problema"}
            ),
            "descricao": Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Descreva o problema com o máximo de detalhes...",
                }
            ),
        }


class EncerrarTicketForm(TailwindFormMixin, ModelForm):
    class Meta:
        model = Ticket
        fields = ["solucao"]
        widgets = {
            "solucao": Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Descreva a solução aplicada...",
                }
            ),
        }


class CancelarTicketForm(TailwindFormMixin, ModelForm):
    class Meta:
        model = Ticket
        fields = ["motivo_cancelamento"]
        widgets = {
            "motivo_cancelamento": Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Explique o motivo do cancelamento...",
                }
            ),
        }
