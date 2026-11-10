from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import *

REGION = 'Región Metropolitana'
COMUNAS = [
    'Santiago', 'Providencia', 'Las Condes', 'La Reina', 'Ñuñoa', 'Maipú', 'Puente Alto', 'La Florida',
    'Peñalolén', 'Quilicura', 'Colina', 'Pudahuel', 'Lo Barnechea', 'Vitacura', 'Lo Prado', 'San Bernardo',
    'San Joaquín', 'Macul', 'Independencia', 'Renca', 'Cerro Navia', 'Conchalí', 'La Cisterna', 'San Miguel',
    'San Ramón', 'Estación Central', 'Padre Hurtado', 'El Bosque', 'La Granja', 'La Pintana', 'Quinta Normal',
    'Peñaflor', 'Lo Espejo', 'Huechuraba', 'Pedro Aguirre Cerda', 'Recoleta',
]
ROLES = ['Cliente', 'Encargado taller', 'Administrador']  # el orden fija los ids 1, 2, 3
ESTADOS_AGENDA = ['En proceso', 'Por pagar', 'Pagado']      # ids 1, 2, 3
ESTADOS_TICKET = ['Pendiente', 'Aceptado', 'Rechazado']
TIPOS_AGENDA = [
    'Mantenimiento programado', 'Reparación urgente', 'Inspección técnica', 'Revisión de frenos',
    'Cambio de aceite', 'Alineación y balanceo', 'Cambio de neumáticos', 'Revisión de suspensión',
    'Diagnóstico de motor',
]
TIPOS_VEHICULO = ['Automóvil', 'Camioneta', 'SUV', 'Furgoneta', 'Pick-up', 'Coupé', 'Sedán', 'Hatchback',
                  'Convertible', 'Station Wagon']
MARCAS = [
    'Audi', 'BMW', 'Chevrolet', 'Citroën', 'Fiat', 'Ford', 'Honda', 'Hyundai', 'Kia', 'Mazda',
    'Mercedes-Benz', 'Mitsubishi', 'Nissan', 'Peugeot', 'Renault', 'Subaru', 'Suzuki', 'Toyota',
    'Volkswagen', 'Volvo', 'Jeep', 'Land Rover', 'MINI', 'Porsche', 'Tesla', 'Lexus', 'Dodge', 'Ram',
]
DEMO_PASSWORD = 'garage360123'

DEMO_TALLERES = [
    ('Mecánica Express Providencia', 'Mantenciones al día, frenos, suspensión y diagnóstico computarizado.',
     'Av. Providencia 1234, Providencia', '+56912345678', 'Providencia', 'demo/taller1.jpg', -33.4260, -70.6180),
    ('Taller Los Andes', 'Especialistas en cambio de aceite, alineación y balanceo con repuestos garantizados.',
     'Av. Apoquindo 4500, Las Condes', '+56923456789', 'Las Condes', 'demo/taller2.jpg', -33.4125, -70.5800),
    ('AutoCenter Ñuñoa', 'Revisión técnica previa, neumáticos y reparaciones urgentes el mismo día.',
     'Av. Irarrázaval 3000, Ñuñoa', '+56934567890', 'Ñuñoa', 'demo/taller3.jpg', -33.4540, -70.6020),
]


class Command(BaseCommand):
    help = 'Carga los catálogos base (roles, comunas, marcas...) y, con --demo, datos de ejemplo.'

    def add_arguments(self, parser):
        parser.add_argument('--demo', action='store_true',
                            help=f'Crea usuarios, talleres y reservas de ejemplo (clave: {DEMO_PASSWORD}).')

    def handle(self, *args, **opts):
        for i, nombre in enumerate(ROLES, 1):
            rolUsuario.objects.get_or_create(idRol=i, defaults={'nombreRol': nombre})
        for i, nombre in enumerate(ESTADOS_AGENDA, 1):
            EstadoAgenda.objects.get_or_create(idEstado=i, defaults={'nombreEstado': nombre})
        for i, nombre in enumerate(ESTADOS_TICKET, 1):
            EstadoTicket.objects.get_or_create(idEstado=i, defaults={'NombreEstado': nombre})
        region, _ = Region.objects.get_or_create(nombreRegion=REGION)
        for nombre in COMUNAS:
            Comuna.objects.get_or_create(nombreComuna=nombre, idRegion=region)
        for nombre in TIPOS_AGENDA:
            TipoAgenda.objects.get_or_create(nombreTipo=nombre)
        for nombre in TIPOS_VEHICULO:
            TipoVehiculo.objects.get_or_create(nombreTipo=nombre)
        for nombre in MARCAS:
            Marca.objects.get_or_create(nombreMarca=nombre)
        self.stdout.write(self.style.SUCCESS('Catálogos base listos.'))

        if opts['demo']:
            self.demo()

    def usuario(self, username, rol, nombre, apellido, comuna, **extra):
        user, creado = UsuarioCustom.objects.get_or_create(username=username, defaults=dict(
            run='11111111-1', correo=f'{username}@garage360.test', email=f'{username}@garage360.test',
            telefono='+56911111111', pnombre=nombre, ap_paterno=apellido, direccion='Calle Demo 123',
            idRol=rolUsuario.objects.get(nombreRol=rol), idComuna=Comuna.objects.get(nombreComuna=comuna),
            **extra))
        if creado:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def demo(self):
        self.usuario('admin', 'Administrador', 'Ana', 'Admin', 'Santiago', is_staff=True, is_superuser=True)
        cliente = self.usuario('cliente', 'Cliente', 'Carlos', 'Cliente', 'Providencia')
        encargados = [
            self.usuario('encargado1', 'Encargado taller', 'Elena', 'Ramírez', 'Providencia'),
            self.usuario('encargado2', 'Encargado taller', 'Mario', 'Soto', 'Las Condes'),
            self.usuario('encargado3', 'Encargado taller', 'Paula', 'Vega', 'Ñuñoa'),
        ]
        talleres = []
        for enc, (nombre, desc, dir_, tel, comuna, img, lat, lng) in zip(encargados, DEMO_TALLERES):
            taller, _ = Taller.objects.get_or_create(nombreTaller=nombre, defaults=dict(
                descripcion=desc, direccion=dir_, telefono=tel, imagen=img, idUsuario=enc,
                idComuna=Comuna.objects.get(nombreComuna=comuna), latitud=lat, longitud=lng))
            talleres.append(taller)

        vehiculo, _ = Vehiculo.objects.get_or_create(patente='ABCD12', defaults=dict(
            modelo='Corolla', anno=2019, idUsuario=cliente,
            idMarca=Marca.objects.get(nombreMarca='Toyota'),
            idTipoVehiculo=TipoVehiculo.objects.get(nombreTipo='Sedán')))

        dia = date.today() + timedelta(days=1)
        while dia.weekday() >= 5:
            dia += timedelta(days=1)
        Agenda.objects.get_or_create(fechaAtencion=dia, horaAtencion='10:00', idTaller=talleres[0], defaults=dict(
            idTipoAgenda=TipoAgenda.objects.get(nombreTipo='Cambio de aceite'),
            idVehiculo=vehiculo, cliente=cliente))
        # Una reserva lista para pagar, un ticket y un mensaje de contacto para ver todas las pantallas
        dia2 = dia + timedelta(days=1)
        while dia2.weekday() >= 5:
            dia2 += timedelta(days=1)
        por_pagar, creada = Agenda.objects.get_or_create(
            fechaAtencion=dia2, horaAtencion='15:00', idTaller=talleres[0], defaults=dict(
                idTipoAgenda=TipoAgenda.objects.get(nombreTipo='Revisión de frenos'),
                idVehiculo=vehiculo, cliente=cliente, estado_id=2))
        ReportePago.objects.get_or_create(reserva=por_pagar, defaults=dict(
            comentario='Cambio de pastillas de freno delanteras y rectificado de discos.', monto=89990))
        Ticket.objects.get_or_create(asunto='Necesito actualizar el horario de atención de mi taller.',
                                     solicitante=encargados[0],
                                     defaults={'EstadoTicket': EstadoTicket.objects.get(NombreEstado='Pendiente')})
        Contacto.objects.get_or_create(correo='maria@example.com', defaults=dict(
            nombre='María González', telefono='+56987654321',
            asunto='¿Pueden agregar más talleres en Maipú? Gracias.'))
        self.stdout.write(self.style.SUCCESS(
            f'Datos demo listos. Usuarios: admin / cliente / encargado1..3  (clave: {DEMO_PASSWORD})'))
