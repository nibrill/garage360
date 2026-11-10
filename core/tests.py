from datetime import date, timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (Agenda, Comuna, Contacto, Marca, ReportePago, Taller, TipoAgenda, TipoVehiculo, Ticket,
                     UsuarioCustom, Vehiculo)


def proximo_dia_habil():
    dia = date.today() + timedelta(days=1)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia


class BaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed', '--demo', verbosity=0)
        cls.taller = Taller.objects.get(nombreTaller='Mecánica Express Providencia')

    def login(self, username):
        self.client.force_login(UsuarioCustom.objects.get(username=username))


class PaginasTest(BaseTest):
    """Todas las páginas responden 200 para el rol que corresponde."""

    PUBLICAS = ['index', 'sobre_nosotros', 'contactanos', 'register', 'login']
    CLIENTE = ['talleres', 'mapa', 'mis_reservas', 'mis_vehiculos', 'annadir_vehiculo', 'perfil_usuario']
    ADMIN = ['administracion', 'administrar_talleres', 'crear_taller', 'administrar_usuarios',
             'crear_usuario', 'tickets', 'mensajes']

    def test_publicas(self):
        for nombre in self.PUBLICAS:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_cliente(self):
        self.login('cliente')
        for nombre in self.CLIENTE:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)
        r = self.client.get(reverse('agendar_hora', args=[self.taller.idTaller]))
        self.assertEqual(r.status_code, 200)
        reserva = Agenda.objects.first()
        self.assertEqual(self.client.get(reverse('detalle_reserva', args=[reserva.idAgenda])).status_code, 200)

    def test_admin(self):
        self.login('admin')
        for nombre in self.ADMIN + self.CLIENTE:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)
        cliente = UsuarioCustom.objects.get(username='cliente')
        self.assertEqual(self.client.get(reverse('modificar_usuario', args=[cliente.id])).status_code, 200)
        self.assertEqual(self.client.get(reverse('modificar_taller', args=[self.taller.idTaller])).status_code, 200)

    def test_encargado(self):
        self.login('encargado1')
        for nombre in ['administrar_mi_taller', 'mis_tickets', 'crear_ticket']:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)
        self.assertEqual(self.client.get(reverse('reservas_taller', args=[self.taller.idTaller])).status_code, 200)


class PermisosTest(BaseTest):
    def test_anonimo_redirige_a_login(self):
        for nombre in ['talleres', 'mapa', 'mis_reservas', 'administracion']:
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302, nombre)
            self.assertIn('/accounts/login/', r['Location'])

    def test_cliente_no_entra_a_administracion(self):
        self.login('cliente')
        for nombre in ['administracion', 'administrar_usuarios', 'administrar_talleres', 'mensajes', 'tickets']:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 403, nombre)

    def test_cliente_no_puede_modificar_usuarios(self):
        self.login('cliente')
        admin = UsuarioCustom.objects.get(username='admin')
        self.assertEqual(self.client.get(reverse('modificar_usuario', args=[admin.id])).status_code, 403)

    def test_eliminar_exige_post_y_rol(self):
        self.login('cliente')
        self.assertEqual(self.client.post(reverse('eliminar_taller', args=[self.taller.idTaller])).status_code, 403)
        self.login('admin')
        self.assertEqual(self.client.get(reverse('eliminar_taller', args=[self.taller.idTaller])).status_code, 405)
        self.assertTrue(Taller.objects.filter(pk=self.taller.pk).exists())

    def test_no_se_toca_vehiculo_ajeno(self):
        vehiculo = Vehiculo.objects.get(patente='ABCD12')
        self.login('encargado1')
        self.assertEqual(self.client.get(reverse('modificar_vehiculo', args=[vehiculo.idVehiculo])).status_code, 403)
        self.assertEqual(self.client.post(reverse('eliminar_vehiculo', args=[vehiculo.idVehiculo])).status_code, 403)
        self.assertTrue(Vehiculo.objects.filter(pk=vehiculo.pk).exists())

    def test_reserva_ajena_no_visible(self):
        reserva = Agenda.objects.first()
        self.login('encargado2')  # encargado de otro taller
        self.assertEqual(self.client.get(reverse('detalle_reserva', args=[reserva.idAgenda])).status_code, 403)
        self.assertEqual(self.client.get(reverse('generar_documento_word', args=[reserva.idAgenda])).status_code, 403)
        self.assertEqual(self.client.post(reverse('actualizar_estado_agenda', args=[reserva.idAgenda])).status_code, 403)

    def test_tickets_solo_admin_y_post(self):
        encargado = UsuarioCustom.objects.get(username='encargado1')
        self.login('encargado1')
        self.client.post(reverse('crear_ticket'), {'asunto': 'Necesito ayuda'})
        ticket = Ticket.objects.filter(solicitante=encargado, asunto='Necesito ayuda').get()
        self.assertEqual(self.client.post(reverse('aceptar_ticket', args=[ticket.idTicket])).status_code, 403)
        self.login('admin')
        self.client.post(reverse('aceptar_ticket', args=[ticket.idTicket]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.EstadoTicket.NombreEstado, 'Aceptado')

    def test_api(self):
        self.assertEqual(self.client.get('/api/usuarios/').status_code, 403)
        self.login('cliente')
        self.assertEqual(self.client.get('/api/usuarios/').status_code, 403)
        self.assertEqual(self.client.get('/api/marcas/').status_code, 200)
        self.assertEqual(self.client.post('/api/marcas/', {'nombreMarca': 'X'}).status_code, 403)
        self.login('admin')
        data = self.client.get('/api/usuarios/').json()
        self.assertNotIn('password', data[0] if isinstance(data, list) else data['results'][0])


class ReservasTest(BaseTest):
    def reservar(self, fecha, hora='11:00'):
        vehiculo = Vehiculo.objects.get(patente='ABCD12')
        return self.client.post(reverse('agendar_hora', args=[self.taller.idTaller]), {
            'fechaAtencion': fecha.isoformat(), 'horaAtencion': hora,
            'idTipoAgenda': TipoAgenda.objects.first().pk, 'idVehiculo': vehiculo.idVehiculo,
        })

    def test_reserva_y_hora_ocupada(self):
        self.login('cliente')
        dia = proximo_dia_habil()
        r = self.reservar(dia)
        errores = r.context['form'].errors if r.status_code == 200 else ''
        self.assertRedirects(r, reverse('mis_reservas'), msg_prefix=str(errores))
        r = self.reservar(dia)  # misma hora: rechazada
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Agenda.objects.filter(fechaAtencion=dia, horaAtencion='11:00').count(), 1)

    def test_rechaza_fin_de_semana_y_pasado(self):
        self.login('cliente')
        sabado = date.today() + timedelta(days=(5 - date.today().weekday()) % 7 or 7)
        self.assertEqual(self.reservar(sabado).status_code, 200)
        self.assertEqual(self.reservar(date.today() - timedelta(days=3)).status_code, 200)
        self.assertEqual(Agenda.objects.filter(horaAtencion='11:00').count(), 0)

    def test_horas_disponibles(self):
        self.login('cliente')
        dia = proximo_dia_habil()
        r = self.client.get(reverse('get_available_hours'), {'date': dia.isoformat(), 'id_taller': self.taller.idTaller})
        self.assertNotIn('10:00', r.json()['available_hours'])  # la reserva demo ocupa las 10:00
        self.assertIn('11:00', r.json()['available_hours'])

    def test_reporte_de_pago_y_pago(self):
        reserva = Agenda.objects.first()
        self.login('encargado1')
        r = self.client.post(reverse('reporte_pago', args=[reserva.idAgenda]),
                             {'comentario': 'Cambio de aceite', 'monto': 25000})
        self.assertEqual(r.status_code, 302)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado_id, 2)
        self.assertTrue(ReportePago.objects.filter(reserva=reserva).exists())
        self.login('cliente')
        r = self.client.post(reverse('actualizar_estado_agenda', args=[reserva.idAgenda]))
        self.assertTrue(r.json()['success'])
        self.assertEqual(self.client.get(reverse('generar_documento_word', args=[reserva.idAgenda])).status_code, 200)


class FormulariosTest(BaseTest):
    def test_registro_crea_cliente(self):
        r = self.client.post(reverse('register'), {
            'username': 'nuevo_user', 'run': '12345678-9', 'correo': 'nuevo@example.com',
            'pnombre': 'Nuevo', 'ap_paterno': 'Usuario', 'direccion': 'Calle 1',
            'comuna': Comuna.objects.first().pk, 'password1': 'Clave-segura-987', 'password2': 'Clave-segura-987',
        })
        self.assertRedirects(r, reverse('login'))
        self.assertEqual(UsuarioCustom.objects.get(username='nuevo_user').idRol.nombreRol, 'Cliente')

    def test_vehiculo_patente_minuscula(self):
        self.login('cliente')
        self.client.post(reverse('annadir_vehiculo'), {
            'patente': 'wxyz99', 'modelo': 'Yaris', 'anno': 2020, 'idMarca': Marca.objects.first().pk,
            'idTipoVehiculo': TipoVehiculo.objects.first().pk})
        self.assertTrue(Vehiculo.objects.filter(patente='WXYZ99').exists())

    def test_contacto_no_requiere_servicios_externos(self):
        self.login('cliente')
        r = self.client.post(reverse('contactanos'), {
            'nombre': 'Ana', 'correo': 'ana@example.com', 'telefono': '+56912345678', 'asunto': 'Hola'})
        self.assertRedirects(r, reverse('contactanos'))
        self.assertTrue(Contacto.objects.filter(correo='ana@example.com').exists())


class SeoTest(BaseTest):
    def test_robots_y_sitemap(self):
        r = self.client.get('/robots.txt')
        self.assertContains(r, 'Sitemap:')
        self.assertContains(r, 'Disallow: /api/')
        r = self.client.get('/sitemap.xml')
        self.assertContains(r, '<urlset')

    def test_metadatos_en_inicio(self):
        r = self.client.get(reverse('index'))
        self.assertContains(r, 'og:title')
        self.assertContains(r, 'Garage360')


class InterfazTest(BaseTest):
    def test_home_tiene_buscador_y_tema(self):
        r = self.client.get(reverse('index'))
        self.assertContains(r, 'role="search"')
        self.assertContains(r, 'data-theme-toggle')
        self.assertContains(r, 'core/js/main.js')

    def test_mapa_entrega_talleres_como_json(self):
        self.login('cliente')
        r = self.client.get(reverse('mapa'))
        self.assertContains(r, 'id="talleres-data"')
        self.assertContains(r, 'Express Providencia')

    def test_pago_en_modo_demo_sin_paypal(self):
        self.login('cliente')
        reserva = Agenda.objects.get(estado_id=2)
        r = self.client.get(reverse('detalle_reserva', args=[reserva.idAgenda]))
        self.assertContains(r, 'btnDemoPago')
        self.assertNotContains(r, 'paypalobjects.com')
