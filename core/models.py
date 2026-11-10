from django.db import models
from django.contrib.auth.models import AbstractUser

#MODELOS RELACIONADOS AL USUARIO:
class rolUsuario(models.Model):
    idRol = models.AutoField(primary_key=True)
    nombreRol = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.nombreRol

    class Meta:
        permissions = (
            ("cliente_permiso", "Permiso para Cliente"),
            ("encargado_taller_permiso", "Permiso para Encargado de Taller"),
            ("administrador_permiso", "Permiso para Administrador"),
        )
    

class Region(models.Model):
    idRegion = models.AutoField(primary_key=True)
    nombreRegion = models.CharField(max_length=80, blank=False, null=False)

    def __str__(self):
        return self.nombreRegion

class Comuna(models.Model):
    idComuna = models.AutoField(primary_key=True)
    nombreComuna = models.CharField(max_length=80, blank=False, null=False)
    idRegion = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombreComuna

class UsuarioCustom(AbstractUser):
    run = models.CharField(max_length=12, blank=False, null=False)
    correo = models.EmailField(blank=False, null=False)
    telefono = models.CharField(max_length=15, blank=False, null=False)
    pnombre = models.CharField(max_length=20, blank=False, null=False)
    ap_paterno = models.CharField(max_length=24, blank=False, null=False)
    direccion = models.CharField(blank=False, null=False, max_length=100)
    idRol = models.ForeignKey(rolUsuario, on_delete=models.CASCADE, blank=True, null=True)
    idComuna = models.ForeignKey(Comuna, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.username
    
class Taller(models.Model):
    idTaller = models.AutoField(primary_key=True)
    nombreTaller = models.CharField(max_length=46, blank=False, null=False)
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=False, null=False)
    telefono = models.CharField(max_length=15, blank=False, null=False)
    imagen = models.ImageField(upload_to='taller_imagenes/', blank=False, null=False)
    idUsuario = models.ForeignKey('UsuarioCustom', on_delete=models.CASCADE, blank=True, null=True)
    idComuna = models.ForeignKey('Comuna', on_delete=models.CASCADE, blank=True, null=True)
    latitud = models.FloatField(blank=True, null=True)
    longitud = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.nombreTaller

#MODELOS RELACIONADOS AL VEHÍCULO:
class Marca(models.Model):
    idMarca = models.AutoField(primary_key=True)
    nombreMarca = models.CharField(max_length=32, blank=False, null=False)

    def __str__(self):
        return self.nombreMarca

class TipoVehiculo(models.Model):
    idTipo= models.AutoField(primary_key=True)
    nombreTipo = models.CharField(max_length=32, blank=False, null=False)

    def __str__(self):
        return self.nombreTipo

class Vehiculo(models.Model):
    idVehiculo = models.AutoField(primary_key=True)
    patente = models.CharField(blank=False, null=False, max_length=6)
    modelo = models.CharField(blank=False, null=False, max_length=20)
    subModelo = models.CharField(blank=True, null=True, max_length=20)
    anno = models.IntegerField(blank=False, null=False)
    idUsuario = models.ForeignKey(UsuarioCustom, on_delete=models.CASCADE, blank=True, null=True)
    idMarca = models.ForeignKey(Marca, on_delete=models.CASCADE, blank=False, null=False)
    idTipoVehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return self.patente

#MODELOS RELACIONADOS A LA AGENDA:
class TipoAgenda(models.Model):
    idTipo= models.AutoField(primary_key=True)
    nombreTipo = models.CharField(max_length=32, blank=False, null=False)

    def __str__(self):
        return self.nombreTipo
    
class EstadoAgenda(models.Model):
    idEstado = models.AutoField(primary_key=True)
    nombreEstado = models.CharField(max_length=50, blank=False, null=False)

    def __str__(self):
        return self.nombreEstado

class Agenda(models.Model):
    idAgenda = models.AutoField(primary_key=True)
    fechaAtencion = models.DateField(null=False, blank=False)
    horaAtencion = models.TimeField(blank=False, null=False)
    idTipoAgenda = models.ForeignKey(TipoAgenda, on_delete=models.CASCADE, blank=False, null=False)
    idTaller = models.ForeignKey(Taller, on_delete=models.CASCADE, blank=False, null=False) 
    idVehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, blank=False, null=False)
    cliente = models.ForeignKey(UsuarioCustom, on_delete=models.CASCADE, blank=False, null=False)
    estado = models.ForeignKey(EstadoAgenda, on_delete=models.CASCADE, blank=True, null=True, default=1) 

    class Meta:
        ordering = ['-fechaAtencion', '-horaAtencion']

    def __str__(self):
        return f'Reserva {self.idAgenda} - {self.fechaAtencion} {self.horaAtencion:%H:%M}'

    
class ReportePago(models.Model):
    idReporte = models.AutoField(primary_key=True)
    reserva = models.OneToOneField(Agenda, on_delete=models.CASCADE)
    comentario = models.TextField(blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Reporte de pago para reserva {self.reserva.idAgenda}"
    
#Modelos relacionados a los tickets
class EstadoTicket(models.Model):
    idEstado = models.AutoField(primary_key=True)
    NombreEstado = models.CharField(max_length=50, blank=False, null=False)

    def __str__(self):
        return self.NombreEstado
    
class Ticket(models.Model):
    idTicket = models.AutoField(primary_key=True)
    asunto = models.TextField(blank=False, null=False)
    solicitante = models.ForeignKey(UsuarioCustom, on_delete=models.CASCADE, blank=False, null=False)
    EstadoTicket = models.ForeignKey(EstadoTicket, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return f'Ticket #{self.idTicket}'
    
class Contacto(models.Model):
    idContacto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, blank=False, null=False)
    correo = models.EmailField(blank=False, null=False)
    telefono = models.CharField(max_length=15, blank=False, null=False)
    asunto = models.TextField(blank=False, null=False)
