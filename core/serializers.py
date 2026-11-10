from rest_framework import serializers
from .models import *

# Serializadores para modelos relacionados al usuario
class RolUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = rolUsuario
        fields = '__all__'

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = '__all__'

class UsuarioCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioCustom
        fields = ['id', 'username', 'run', 'correo', 'telefono', 'pnombre', 'ap_paterno',
                  'direccion', 'idRol', 'idComuna', 'is_active']

class TallerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taller
        fields = '__all__'

# Serializadores para modelos relacionados al vehículo
class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'

class TipoVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoVehiculo
        fields = '__all__'

class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'

# Serializadores para modelos relacionados a la agenda
class TipoAgendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAgenda
        fields = '__all__'

class AgendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agenda
        fields = '__all__'

