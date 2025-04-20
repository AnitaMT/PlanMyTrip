from django import forms
from django.contrib.auth.forms import UserCreationForm

from viajes.models import UsuarioPersonalizado, Viaje, Destino, Actividad


class RegistroUsuarioForm(UserCreationForm):
    class Meta:
        model = UsuarioPersonalizado
        fields = ['username', 'email', 'password1', 'password2']


class CrearViajeForm(forms.ModelForm):
    destino_nombre = forms.CharField(
        max_length=255,
        label="Nombre del destino (ej: Cancún, México)",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Escribe el nombre del destino y el país separados por coma"
    )

    categoria_destino = forms.ChoiceField(
        choices=Destino.CATEGORIAS_DESTINO,
        label="Tipo de destino",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Viaje
        fields = ['nombre', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AgregarActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'descripcion', 'fecha_hora', 'ubicacion', 'prioridad', 'categoria', 'coste_estimado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'coste_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
        }