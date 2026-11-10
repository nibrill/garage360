from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(rolUsuario)
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(UsuarioCustom)
admin.site.register(Taller)
admin.site.register(Marca)
admin.site.register(TipoVehiculo)
admin.site.register(Vehiculo)
admin.site.register(TipoAgenda)
admin.site.register(EstadoAgenda)
admin.site.register(Agenda)
admin.site.register(ReportePago)