from datetime import time
from decimal import Decimal
from functools import wraps
from io import BytesIO

import docx
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from .forms import *
from .geo import geocodificar, sugerencias
from .models import *
from .serializers import *

ROL_ADMIN = 'Administrador'
ROL_ENCARGADO = 'Encargado taller'
ROL_CLIENTE = 'Cliente'


def _rol(user):
    return user.idRol.nombreRol if user.is_authenticated and user.idRol else None


def es_admin(user):
    return user.is_authenticated and (user.is_superuser or _rol(user) == ROL_ADMIN)


def role_required(roles):
    """Exige sesión iniciada y alguno de los roles indicados (el superusuario siempre pasa)."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'{settings.LOGIN_URL}?next={request.path}')
            if request.user.is_superuser or _rol(request.user) in roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('No tienes permiso para acceder a esta página')
        return _wrapped_view
    return decorator


# ----------------------------------------------------------------------------
# API REST
# ----------------------------------------------------------------------------
class LecturaAutenticadaEscrituraAdmin(permissions.BasePermission):
    """Catálogos: lectura con sesión iniciada, escritura solo administradores."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return es_admin(request.user)


class SoloAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return es_admin(request.user)


class CatalogoViewSet(viewsets.ModelViewSet):
    permission_classes = [LecturaAutenticadaEscrituraAdmin]


class RolUsuarioViewSet(CatalogoViewSet):
    queryset = rolUsuario.objects.all()
    serializer_class = RolUsuarioSerializer


class RegionViewSet(CatalogoViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class ComunaViewSet(CatalogoViewSet):
    queryset = Comuna.objects.all()
    serializer_class = ComunaSerializer


class UsuarioCustomViewSet(viewsets.ModelViewSet):
    permission_classes = [SoloAdmin]
    queryset = UsuarioCustom.objects.all()
    serializer_class = UsuarioCustomSerializer


class TallerViewSet(CatalogoViewSet):
    queryset = Taller.objects.all()
    serializer_class = TallerSerializer


class MarcaViewSet(CatalogoViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer


class TipoVehiculoViewSet(CatalogoViewSet):
    queryset = TipoVehiculo.objects.all()
    serializer_class = TipoVehiculoSerializer


class VehiculoViewSet(viewsets.ModelViewSet):
    """Cada usuario ve solo sus vehículos; el administrador ve todos."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VehiculoSerializer

    def get_queryset(self):
        qs = Vehiculo.objects.all()
        return qs if es_admin(self.request.user) else qs.filter(idUsuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(idUsuario=self.request.user)


class TipoAgendaViewSet(CatalogoViewSet):
    queryset = TipoAgenda.objects.all()
    serializer_class = TipoAgendaSerializer


class AgendaViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura: cada cliente ve sus reservas, el encargado las de su taller."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AgendaSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Agenda.objects.all()
        if es_admin(user):
            return qs
        if _rol(user) == ROL_ENCARGADO:
            return qs.filter(idTaller__idUsuario=user)
        return qs.filter(cliente=user)


# ----------------------------------------------------------------------------
# Páginas públicas
# ----------------------------------------------------------------------------
def index(request):
    return render(request, 'core/index.html', {
        'talleres_destacados': Taller.objects.select_related('idComuna')[:3],
        'total_talleres': Taller.objects.count(),
    })


def sobre_nosotros(request):
    return render(request, 'core/sobre_nosotros.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.idRol, _ = rolUsuario.objects.get_or_create(nombreRol=ROL_CLIENTE)
        user.idComuna = form.cleaned_data['comuna']
        user.email = form.cleaned_data['correo']
        user.save()
        messages.success(request, 'Cuenta creada. Ya puedes iniciar sesión.')
        return redirect('login')
    return render(request, 'registration/register.html', {'form': form})


def contactanos(request):
    form = ContactoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Mensaje enviado correctamente.')
            return redirect('contactanos')
        messages.error(request, 'Hay algún problema con los datos ingresados, revise nuevamente.')
    return render(request, 'core/contactanos.html', {'form': form})


# ----------------------------------------------------------------------------
# Talleres, mapa y geolocalización
# ----------------------------------------------------------------------------
@login_required
def talleres(request):
    qs = Taller.objects.select_related('idComuna')
    q = request.GET.get('q', '').strip()
    comuna = request.GET.get('comuna', '').strip()
    if q:
        qs = qs.filter(Q(nombreTaller__icontains=q) | Q(descripcion__icontains=q) | Q(direccion__icontains=q))
    if comuna.isdigit():
        qs = qs.filter(idComuna_id=int(comuna))
    return render(request, 'core/talleres.html', {
        'talleres': qs,
        'q': q,
        'comuna_sel': comuna,
        'comunas': Comuna.objects.filter(taller__isnull=False).distinct().order_by('nombreComuna'),
    })


@login_required
def mapa(request):
    talleres = Taller.objects.all()
    talleres_json = serialize('json', talleres, fields=('nombreTaller', 'direccion', 'latitud', 'longitud'))
    return render(request, 'core/mapa.html', {'talleres_json': talleres_json})


@role_required([ROL_ADMIN])
def administrar_talleres(request):
    return render(request, 'core/administrar_talleres.html', {'talleres': Taller.objects.all()})


@role_required([ROL_ADMIN])
def crear_taller(request):
    form = TallerForm()
    if request.method == 'POST':
        if 'obtener_ubicacion' in request.POST:
            address = request.POST.get('address')
            coords, error = geocodificar(address)
            if error:
                return JsonResponse({'success': False, 'error': error})
            return JsonResponse({'success': True, 'coordinates': coords, 'address': address})
        form = TallerForm(request.POST, request.FILES)
        if form.is_valid():
            taller = form.save(commit=False)
            latitud = request.POST.get('latitud')
            longitud = request.POST.get('longitud')
            direccion = request.POST.get('direccion')
            try:
                if latitud and longitud:
                    taller.latitud = float(latitud)
                    taller.longitud = float(longitud)
            except ValueError:
                pass
            if direccion:
                taller.direccion = direccion
            taller.save()
            return redirect('administrar_talleres')
    return render(request, 'core/crear_taller.html', {'form': form, 'coordinates': {}, 'address': ''})


@role_required([ROL_ADMIN])
def modificar_taller(request, id_taller):
    taller = get_object_or_404(Taller, idTaller=id_taller)
    if request.method == 'POST':
        if 'obtener_ubicacion' in request.POST:
            address = request.POST.get('address')
            coords, error = geocodificar(address)
            if error:
                return JsonResponse({'success': False, 'error': error})
            taller.direccion = address
            taller.latitud, taller.longitud = coords['lat'], coords['lng']
            taller.save()
            return JsonResponse({'success': True, 'coordinates': coords, 'address': address})
        form = TallerForm(request.POST, request.FILES, instance=taller)
        if form.is_valid():
            modificado = form.save(commit=False)
            if request.POST.get('direccion'):
                modificado.direccion = request.POST['direccion']
            modificado.save()
            return redirect('administrar_talleres')
    else:
        form = TallerForm(instance=taller)
    return render(request, 'core/modificar_taller.html', {'form': form, 'taller': taller})


@role_required([ROL_ADMIN])
@require_POST
def eliminar_taller(request, id_taller):
    get_object_or_404(Taller, idTaller=id_taller).delete()
    return redirect('administrar_talleres')


@role_required([ROL_ADMIN])
def get_coordinates(request):
    """Página de prueba para geocodificar direcciones."""
    form = AddressForm(request.POST or None)
    ctx = {'form': form}
    if request.method == 'POST' and form.is_valid():
        coords, error = geocodificar(form.cleaned_data['address'])
        if error:
            ctx['error_message'] = error
        else:
            ctx.update(coordinates=coords, success_message='La dirección seleccionada es válida')
    return render(request, 'core/test.html', ctx)


def autocomplete_address(request):
    term = request.GET.get('term', '').strip()
    if len(term) < 3:
        return JsonResponse([], safe=False)
    return JsonResponse(sugerencias(term), safe=False)


# ----------------------------------------------------------------------------
# Reservas
# ----------------------------------------------------------------------------
@login_required
def agendar_hora(request, id_taller):
    taller = get_object_or_404(Taller, idTaller=id_taller)
    if request.method == 'POST':
        form = AgendaForm(request.POST, user=request.user, taller=taller)
        if form.is_valid():
            agenda = form.save(commit=False)
            agenda.idTaller = taller
            agenda.cliente = request.user
            agenda.save()
            messages.success(request, 'Tu hora fue reservada.')
            return redirect('mis_reservas')
    else:
        form = AgendaForm(user=request.user, taller=taller)
    return render(request, 'core/agendar_hora.html', {'form': form, 'taller': taller})


@login_required
def get_available_hours(request):
    fecha = request.GET.get('date')
    taller = get_object_or_404(Taller, idTaller=request.GET.get('id_taller'))
    ocupadas = set()
    if fecha:
        ocupadas = set(Agenda.objects.filter(fechaAtencion=fecha, idTaller=taller)
                       .values_list('horaAtencion', flat=True))
    horas = [f'{h:02}:00' for h in range(9, 19) if time(hour=h) not in ocupadas]
    return JsonResponse({'available_hours': horas})


@login_required
def mis_reservas(request):
    agendas = (Agenda.objects.filter(cliente=request.user)
               .select_related('idTaller', 'idVehiculo', 'idTipoAgenda', 'estado')
               .order_by('-fechaAtencion', '-horaAtencion'))
    return render(request, 'core/mis_reservas.html', {'agendas': agendas})


def _puede_ver_reserva(user, agenda):
    return (es_admin(user) or agenda.cliente_id == user.id
            or (_rol(user) == ROL_ENCARGADO and agenda.idTaller.idUsuario_id == user.id))


@login_required
def detalle_reserva(request, id_agenda):
    agenda = get_object_or_404(Agenda, idAgenda=id_agenda)
    if not _puede_ver_reserva(request.user, agenda):
        return HttpResponseForbidden('No tienes permiso para ver esta reserva')
    reporte_pago = ReportePago.objects.filter(reserva=agenda).first()

    monto_dolares = None
    if reporte_pago:
        try:
            tasa = Decimal(str(requests.get('https://mindicador.cl/api/', timeout=5).json()['dolar']['valor']))
            monto_dolares = format(round(Decimal(reporte_pago.monto) / tasa, 2), '.2f')
        except (requests.RequestException, ValueError, KeyError, ArithmeticError):
            monto_dolares = None

    return render(request, 'core/detalle_reserva.html', {
        'agenda': agenda, 'reporte_pago': reporte_pago, 'monto_dolares': monto_dolares,
    })


@login_required
@require_POST
def actualizar_estado_agenda(request, id_agenda):
    agenda = get_object_or_404(Agenda, idAgenda=id_agenda)
    if agenda.cliente_id != request.user.id and not es_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
    estado = EstadoAgenda.objects.filter(nombreEstado='Pagado').first()
    if not estado:
        return JsonResponse({'success': False, 'error': 'Estado "Pagado" no encontrado'}, status=400)
    agenda.estado = estado
    agenda.save()
    return JsonResponse({'success': True, 'filename': f'Reserva_{agenda.idAgenda}.docx'})


@login_required
def generar_documento_word(request, id_agenda):
    agenda = get_object_or_404(Agenda, idAgenda=id_agenda)
    if not _puede_ver_reserva(request.user, agenda):
        return HttpResponseForbidden('No tienes permiso para ver esta reserva')

    documento = docx.Document()
    documento.add_heading('Detalle de la Reserva', level=1)
    documento.add_paragraph(f'Fecha de Atención: {agenda.fechaAtencion}')
    documento.add_paragraph(f'Hora de Atención: {agenda.horaAtencion}')
    documento.add_paragraph(f'Tipo de Agenda: {agenda.idTipoAgenda}')
    documento.add_paragraph(f'Taller: {agenda.idTaller}')
    documento.add_paragraph(f'Patente Vehículo: {agenda.idVehiculo}')
    reporte = ReportePago.objects.filter(reserva=agenda).first()
    if reporte:
        documento.add_heading('Detalle del Reporte de Pago', level=2)
        documento.add_paragraph(f'Comentario: {reporte.comentario}')
        documento.add_paragraph(f'Monto a pagar: ${reporte.monto}')

    buffer = BytesIO()
    documento.save(buffer)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=Reserva_{agenda.idAgenda}.docx'
    return response


# ----------------------------------------------------------------------------
# Vehículos
# ----------------------------------------------------------------------------
@login_required
def mis_vehiculos(request):
    vehiculos = Vehiculo.objects.filter(idUsuario=request.user).select_related('idMarca', 'idTipoVehiculo')
    return render(request, 'core/mis_vehiculos.html', {'vehiculos': vehiculos})


@login_required
def annadir_vehiculo(request):
    form = VehiculoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vehiculo = form.save(commit=False)
        vehiculo.idUsuario = request.user
        vehiculo.save()
        return redirect('mis_vehiculos')
    return render(request, 'core/annadir_vehiculo.html', {'form': form})


@login_required
def modificar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, idVehiculo=vehiculo_id)
    if vehiculo.idUsuario_id != request.user.id and not es_admin(request.user):
        return HttpResponseForbidden('Este vehículo no es tuyo')
    form = VehiculoForm(request.POST or None, instance=vehiculo)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('mis_vehiculos')
    return render(request, 'core/modificar_vehiculo.html', {'form': form})


@login_required
@require_POST
def eliminar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, idVehiculo=vehiculo_id)
    if vehiculo.idUsuario_id != request.user.id and not es_admin(request.user):
        return HttpResponseForbidden('Este vehículo no es tuyo')
    vehiculo.delete()
    return redirect('mis_vehiculos')


# ----------------------------------------------------------------------------
# Administración de usuarios
# ----------------------------------------------------------------------------
@role_required([ROL_ADMIN])
def administracion(request):
    resumen = [
        {'label': 'Usuarios', 'valor': UsuarioCustom.objects.count()},
        {'label': 'Talleres', 'valor': Taller.objects.count()},
        {'label': 'Reservas', 'valor': Agenda.objects.count()},
        {'label': 'Tickets pendientes', 'valor': Ticket.objects.filter(EstadoTicket__NombreEstado='Pendiente').count()},
    ]
    return render(request, 'core/administracion.html', {'resumen': resumen})


@role_required([ROL_ADMIN])
def administrar_usuarios(request):
    return render(request, 'core/administrar_usuarios.html', {'usuarios': UsuarioCustom.objects.select_related('idRol')})


@role_required([ROL_ADMIN])
def modificar_usuario(request, id):
    usuario = get_object_or_404(UsuarioCustom, id=id)
    form = UsuarioCustomForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('administrar_usuarios')
    return render(request, 'core/modificar_usuario.html', {'form': form})


@role_required([ROL_ADMIN])
@require_POST
def eliminar_usuario(request, id):
    usuario = get_object_or_404(UsuarioCustom, id=id)
    if usuario.id == request.user.id:
        return JsonResponse({'success': False, 'error': 'No puedes eliminar tu propia cuenta'}, status=400)
    usuario.delete()
    return JsonResponse({'success': True})


@role_required([ROL_ADMIN])
def crear_usuario(request):
    form = UsuarioCustomCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('administrar_usuarios')
    return render(request, 'core/crear_usuario.html', {'form': form})


@login_required
def perfil_usuario(request):
    form = UsuarioCustomPerfilForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '¡Perfil actualizado correctamente!')
        return redirect('index')
    return render(request, 'core/perfil_usuario.html', {'form': form})


# ----------------------------------------------------------------------------
# Encargado de taller
# ----------------------------------------------------------------------------
@role_required([ROL_ENCARGADO])
def administrar_mi_taller(request):
    return render(request, 'core/administrar_mi_taller.html', {
        'taller': Taller.objects.filter(idUsuario=request.user).first(),
    })


@role_required([ROL_ENCARGADO, ROL_ADMIN])
def reservas_taller(request, idTaller):
    taller = get_object_or_404(Taller, pk=idTaller)
    if not es_admin(request.user) and taller.idUsuario_id != request.user.id:
        return HttpResponseForbidden('Este taller no es tuyo')
    reservas = (Agenda.objects.filter(idTaller=taller)
                .select_related('idVehiculo', 'idTipoAgenda', 'estado', 'cliente')
                .order_by('-fechaAtencion', '-horaAtencion'))
    return render(request, 'core/reservas_taller.html', {'taller': taller, 'reservas': reservas})


@role_required([ROL_ENCARGADO, ROL_ADMIN])
def generar_reporte_pago(request, idReserva):
    reserva = get_object_or_404(Agenda, pk=idReserva)
    if not es_admin(request.user) and reserva.idTaller.idUsuario_id != request.user.id:
        return HttpResponseForbidden('Esta reserva no pertenece a tu taller')
    if ReportePago.objects.filter(reserva=reserva).exists():
        messages.info(request, 'Esta reserva ya tiene un reporte de pago.')
        return redirect('reservas_taller', idTaller=reserva.idTaller.idTaller)
    form = ReportePagoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reporte = form.save(commit=False)
        reporte.reserva = reserva
        reporte.save()
        reserva.estado_id = 2  # "Pendiente de pago"
        reserva.save()
        return redirect('reservas_taller', idTaller=reserva.idTaller.idTaller)
    return render(request, 'core/generar_reporte_pago.html', {'form': form, 'reserva': reserva})


# ----------------------------------------------------------------------------
# Tickets (encargados -> administradores) y mensajes de contacto
# ----------------------------------------------------------------------------
@role_required([ROL_ENCARGADO])
def mis_tickets(request):
    return render(request, 'core/mis_tickets.html', {
        'tickets_usuario': Ticket.objects.filter(solicitante=request.user).select_related('EstadoTicket'),
    })


@role_required([ROL_ENCARGADO])
def crear_ticket(request):
    form = TicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.solicitante = request.user
        ticket.EstadoTicket, _ = EstadoTicket.objects.get_or_create(NombreEstado='Pendiente')
        ticket.save()
        return redirect('mis_tickets')
    return render(request, 'core/crear_ticket.html', {'form': form})


@role_required([ROL_ADMIN])
def tickets(request):
    return render(request, 'core/tickets.html', {'tickets': Ticket.objects.select_related('solicitante', 'EstadoTicket')})


def _resolver_ticket(idTicket, estado):
    ticket = get_object_or_404(Ticket, idTicket=idTicket)
    ticket.EstadoTicket, _ = EstadoTicket.objects.get_or_create(NombreEstado=estado)
    ticket.save()
    return redirect('tickets')


@role_required([ROL_ADMIN])
@require_POST
def aceptar_ticket(request, idTicket):
    return _resolver_ticket(idTicket, 'Aceptado')


@role_required([ROL_ADMIN])
@require_POST
def rechazar_ticket(request, idTicket):
    return _resolver_ticket(idTicket, 'Rechazado')


@role_required([ROL_ADMIN])
def mensajes(request):
    return render(request, 'core/mensajes.html', {'mensajes': Contacto.objects.all()})


@role_required([ROL_ADMIN])
@require_POST
def eliminar_mensaje(request, id_mensaje):
    get_object_or_404(Contacto, idContacto=id_mensaje).delete()
    return redirect('mensajes')


# ----------------------------------------------------------------------------
# SEO
# ----------------------------------------------------------------------------
def robots_txt(request):
    lineas = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /api/',
        'Disallow: /accounts/',
        f'Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse(chr(10).join(lineas) + chr(10), content_type='text/plain')


def sitemap_xml(request):
    base = f'{request.scheme}://{request.get_host()}'
    urls = ['/', '/sobre_nosotros/', '/contactanos/', '/register/']
    cuerpo = ''.join(f'<url><loc>{base}{u}</loc></url>' for u in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{cuerpo}</urlset>'
    return HttpResponse(xml, content_type='application/xml')
