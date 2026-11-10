from django.contrib import admin
from .models import Ticket, Comentario, Historico

# Register your models here.
admin.site.register(Ticket)
admin.site.register(Comentario)
admin.site.register(Historico)