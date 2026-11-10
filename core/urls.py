from django.urls import path, include
from .views import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'roles', RolUsuarioViewSet)
router.register(r'regiones', RegionViewSet)
router.register(r'comunas', ComunaViewSet)
router.register(r'usuarios', UsuarioCustomViewSet)
router.register(r'talleres', TallerViewSet)
router.register(r'marcas', MarcaViewSet)
router.register(r'tipos-vehiculo', TipoVehiculoViewSet)
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
router.register(r'tipos-agenda', TipoAgendaViewSet)
router.register(r'agendas', AgendaViewSet, basename='agenda')

urlpatterns = [
    path('api/', include(router.urls)),
    
    path('', index, name="index"),
    path('robots.txt', robots_txt, name="robots"),
    path('sitemap.xml', sitemap_xml, name="sitemap"),
    path('contactanos/', contactanos, name="contactanos"),
    path('mapa/', mapa, name="mapa"),
    path('mis_reservas/', mis_reservas, name="mis_reservas"),
    path('mis_vehiculos/', mis_vehiculos, name="mis_vehiculos"),
    path('register/', register, name="register"),
    path('sobre_nosotros/', sobre_nosotros, name="sobre_nosotros"),
    path('talleres/', talleres, name="talleres"),
    path('tickets/', tickets, name="tickets"),
    #PANEL DE ADMINISTRACIÓN
    path('administracion/', administracion, name="administracion"),
    
    #ADMINISTRAR TALLERES (CRUD):
    path('administrar_talleres/', administrar_talleres, name="administrar_talleres"),
    path('crear_taller/', crear_taller, name="crear_taller"),
    path('modificar_taller/<int:id_taller>/', modificar_taller, name="modificar_taller"),
    path('eliminar_taller/<int:id_taller>/', eliminar_taller, name='eliminar_taller'),

    # testeo
    path('test/', get_coordinates, name="test"),
    path('autocomplete_address/', autocomplete_address, name='autocomplete_address'),

    #Agendar
    path('agendar_hora/<int:id_taller>/', agendar_hora, name='agendar_hora'),
    path('get_available_hours/', get_available_hours, name='get_available_hours'),

    path('annadir_vehiculo/', annadir_vehiculo, name="annadir_vehiculo"),
    path('modificar_vehiculo/<int:vehiculo_id>/', modificar_vehiculo, name='modificar_vehiculo'),
    path('eliminar_vehiculo/<int:vehiculo_id>/', eliminar_vehiculo, name="eliminar_vehiculo"),

    path('administrar_usuarios/', administrar_usuarios, name="administrar_usuarios"),
    path('modificar_usuario/<int:id>/', modificar_usuario, name='modificar_usuario'),
    path('eliminar_usuario/<int:id>/', eliminar_usuario, name='eliminar_usuario'),
    path('crear_usuario/', crear_usuario, name='crear_usuario'),

    path('administrar_mi_taller/', administrar_mi_taller, name="administrar_mi_taller"),
    path('reservas_taller/<int:idTaller>/', reservas_taller, name='reservas_taller'),

    path('perfil_usuario/', perfil_usuario, name='perfil_usuario'),

    path('reporte_pago/<int:idReserva>/', generar_reporte_pago, name='reporte_pago'),

    path('detalle_reserva/<int:id_agenda>/', detalle_reserva, name='detalle_reserva'),

    path('actualizar_estado_agenda/<int:id_agenda>/', actualizar_estado_agenda, name='actualizar_estado_agenda'),
    path('generar_documento_word/<int:id_agenda>/', generar_documento_word, name='generar_documento_word'),

    path('mis_tickets/', mis_tickets, name="mis_tickets"),

    path('crear_ticket/', crear_ticket, name="crear_ticket"),
    path('aceptar_ticket/<int:idTicket>/', aceptar_ticket, name="aceptar_ticket"),
    path('rechazar_ticket/<int:idTicket>/', rechazar_ticket, name="rechazar_ticket"),

    path('mensajes/', mensajes, name='mensajes'),
    path('eliminar_mensaje/<int:id_mensaje>/', eliminar_mensaje, name='eliminar_mensaje'),
]