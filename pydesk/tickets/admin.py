from django.contrib import admin
from .models import Ativo, Ticket, Comentario

# Register your models here.
admin.site.register(Ativo)
admin.site.register(Ticket)
admin.site.register(Comentario)