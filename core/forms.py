from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from datetime import date, datetime, time
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class AddressForm(forms.Form):
    address = forms.CharField(label='Ingrese dirección', max_length=255)


#REGISTRAR USUARIO:
class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Nombre de usuario', help_text='Mínimo 6 caracteres')
    run = forms.CharField(label='RUN (Rol Único Nacional)', help_text='Ejemplo: 12345678-9')
    correo = forms.EmailField(label='Correo electrónico', help_text='Ejemplo: ejemplo@gmail.com')
    pnombre = forms.CharField(label='Primer Nombre', help_text='Ejemplo: Fabian')
    ap_paterno = forms.CharField(label='Apellido Paterno', help_text='Ejemplo: Ruiz')
    direccion = forms.CharField(label='Dirección', widget=forms.TextInput(attrs={'placeholder': 'Calle, número'}))
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.all(), label='Comuna')

    class Meta:
        model = UsuarioCustom
        fields = ['username', 'run', 'correo', 'pnombre', 'ap_paterno', 'direccion', 'comuna']

#FORMULARIO TALLER:
class TallerForm(forms.ModelForm):
    class Meta:
        model = Taller
        fields = ['nombreTaller', 'descripcion', 'telefono', 'idComuna', 'idUsuario', 'imagen']
        labels = {
            'nombreTaller': 'Nombre del taller',
            'descripcion': 'Descripción',
            'telefono': 'Teléfono',
            'idComuna': 'Comuna',
            'idUsuario': 'Encargado del taller',
            'imagen': 'Imagen',
        }

    telefono = forms.CharField(
        max_length=12,
        validators=[
            RegexValidator(
                regex=r'^\+569\d{8}$',
                message='El número de teléfono debe estar en el formato correcto: +569XXXXXXXX.',
                code='invalid_phone_number'
            )
        ],
        widget=forms.TextInput(attrs={'placeholder': '+56991005929'})
    )

    def __init__(self, *args, **kwargs):
        super(TallerForm, self).__init__(*args, **kwargs)
        self.fields['idUsuario'].queryset = UsuarioCustom.objects.filter(idRol__nombreRol='Encargado taller')
        self.fields['nombreTaller'].required = True
        self.fields['descripcion'].required = True
        self.fields['telefono'].required = True
        self.fields['idComuna'].required = True
        self.fields['idUsuario'].required = True
        self.fields['imagen'].required = True

class AgendaForm(forms.ModelForm):
    class Meta:
        model = Agenda
        fields = ['fechaAtencion', 'horaAtencion', 'idTipoAgenda', 'idVehiculo']
        labels = {
            'fechaAtencion': 'Fecha de Atención (Solo de lunes a viernes)',
            'horaAtencion': 'Hora de Atención',
            'idTipoAgenda': 'Tipo de Agenda',
            'idVehiculo': 'Vehículo',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.taller = kwargs.pop('taller', None)
        super(AgendaForm, self).__init__(*args, **kwargs)

        self.fields['fechaAtencion'].widget = forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()})
        self.fields['horaAtencion'].widget = forms.Select(choices=self.get_available_hours())

        if user:
            self.fields['idVehiculo'].queryset = Vehiculo.objects.filter(idUsuario=user)
        
    def get_available_hours(self):
        available_hours = [(time(hour=h), f"{h:02}:00") for h in range(9, 19)]
        if self.is_bound and 'fechaAtencion' in self.data:
            selected_date = self.data.get('fechaAtencion')
            if selected_date:
                reserved_hours = Agenda.objects.filter(
                    fechaAtencion=selected_date,
                    idTaller=self.taller
                ).values_list('horaAtencion', flat=True)
                available_hours = [
                    (time(hour=h), f"{h:02}:00") for h in range(9, 19)
                    if time(hour=h) not in reserved_hours
                ]
        return available_hours

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fechaAtencion')
        hora = cleaned_data.get('horaAtencion')

        if fecha and hora and self.taller:
            if fecha < date.today():
                raise forms.ValidationError("No puedes reservar en una fecha pasada.")
            if fecha.weekday() >= 5:
                raise forms.ValidationError("Las reservas solo están disponibles de lunes a viernes.")

            if Agenda.objects.filter(fechaAtencion=fecha, horaAtencion=hora, idTaller=self.taller).exists():
                raise forms.ValidationError("La hora seleccionada ya está reservada. Por favor, elija otra hora.")

        return cleaned_data

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        exclude = ['idUsuario']
        labels = {
            'patente': 'Patente del Vehículo',
            'modelo': 'Modelo',
            'subModelo': 'Sub-Modelo',
            'anno': 'Año',
            'idMarca': 'Marca',
            'idTipoVehiculo': 'Tipo de Vehículo',
        }
        widgets = {
            'anno': forms.NumberInput(attrs={'min': 1950, 'max': date.today().year + 1}),
        }

    anno = forms.IntegerField(
        validators=[MinValueValidator(1950), MaxValueValidator(date.today().year + 1)],
        widget=forms.NumberInput(attrs={'min': 1950, 'max': date.today().year + 1}),
        label= 'Año'
    )

    patente = forms.CharField(
        max_length=6,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{4}\d{2}$',
                message='La patente debe estar en el formato correcto: 4 letras seguidas de 2 números (ej. HYRG34).',
                code='invalid_patente',
                flags=re.IGNORECASE
            )
        ],
        widget=forms.TextInput(attrs={'placeholder': 'HYRG34', 'style': 'text-transform:uppercase'})
    )

    def clean_patente(self):
        return self.cleaned_data['patente'].upper()


class UsuarioCustomForm(forms.ModelForm):
    class Meta:
        model = UsuarioCustom
        fields = ['username','run', 'correo', 'pnombre', 'ap_paterno', 'direccion', 'idRol', 'idComuna']
        labels = {
            'username': 'Nombre de usuario',
            'run': 'RUN',
            'correo': 'Correo Electrónico',
            'pnombre': 'Primer Nombre',
            'ap_paterno': 'Apellido Paterno',
            'direccion': 'Dirección',
            'idRol': 'Rol',
            'idComuna': 'Comuna',
        }
        widgets = {
            'run': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'pnombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ap_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'idRol': forms.Select(attrs={'class': 'form-control'}),
            'idComuna': forms.Select(attrs={'class': 'form-control'}),
        }

class UsuarioCustomCreationForm(UserCreationForm):
    username = forms.CharField(max_length=150, label='Nombre de usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    run = forms.CharField(max_length=12, label='RUN', widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo = forms.EmailField(label='Correo Electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    pnombre = forms.CharField(max_length=20, label='Primer Nombre', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ap_paterno = forms.CharField(max_length=24, label='Apellido Paterno', widget=forms.TextInput(attrs={'class': 'form-control'}))
    direccion = forms.CharField(max_length=100, label='Dirección', widget=forms.TextInput(attrs={'class': 'form-control'}))
    idRol = forms.ModelChoiceField(queryset=rolUsuario.objects.all(), label='Rol', widget=forms.Select(attrs={'class': 'form-control'}))
    idComuna = forms.ModelChoiceField(queryset=Comuna.objects.all(), label='Comuna', widget=forms.Select(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = UsuarioCustom
        fields = ['username', 'run', 'correo', 'pnombre', 'ap_paterno', 'direccion', 'idRol', 'idComuna', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
    
class UsuarioCustomPerfilForm(forms.ModelForm):
    class Meta:
        model = UsuarioCustom
        fields = ['username','run', 'correo', 'pnombre', 'ap_paterno', 'direccion', 'idComuna']
        labels = {
            'username': 'Nombre de usuario',
            'run': 'RUN',
            'correo': 'Correo Electrónico',
            'pnombre': 'Primer Nombre',
            'ap_paterno': 'Apellido Paterno',
            'direccion': 'Dirección',
            'idComuna': 'Comuna',
        }
        widgets = {
            'run': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'pnombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ap_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'idComuna': forms.Select(attrs={'class': 'form-control'}),
        }

class ReportePagoForm(forms.ModelForm):
    class Meta:
        model = ReportePago
        fields = ['comentario', 'monto']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'min': 100}),
        }

    def clean_comentario(self):
        comentario = self.cleaned_data.get('comentario')
        if not comentario:
            raise forms.ValidationError('Este campo es obligatorio.')
        return comentario

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is None or monto < 100:
            raise forms.ValidationError('El monto debe ser al menos 100 pesos chilenos.')
        return monto
    
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['asunto']
        widgets = {
            'asunto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_asunto(self):
        comentario = self.cleaned_data.get('asunto')
        if not comentario:
            raise forms.ValidationError('Este campo es obligatorio.')
        return comentario

class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = '__all__'

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise forms.ValidationError("Este campo es obligatorio.")
        return nombre

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if not correo:
            raise forms.ValidationError("Este campo es obligatorio.")
        try:
            validate_email(correo)
        except ValidationError:
            raise forms.ValidationError("Ingrese una dirección de correo válida.")
        
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not re.match(r'^\+569\d{8}$', telefono):
            raise forms.ValidationError("El número de teléfono debe tener el formato +569 seguido de 8 dígitos.")
        return telefono

    def clean_asunto(self):
        asunto = self.cleaned_data.get('asunto')
        if not asunto:
            raise forms.ValidationError("Este campo es obligatorio.")
        return asunto

