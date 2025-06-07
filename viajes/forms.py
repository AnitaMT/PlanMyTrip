from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

from viajes.models import UsuarioPersonalizado, Viaje, Destino, Actividad


class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario para el registro de nuevos usuarios.

    Extiende el UserCreationForm de Django para usar el modelo
    UsuarioPersonalizado, que es personalizado. Incluye validación automática
    de contraseñas y verificación de que el nombre de usuario sea único.

    Campos:
        - username: Nombre de usuario único
        - email: Correo electrónico del usuario
        - password1: Contraseña inicial
        - password2: Confirmación de contraseña
    """
    class Meta:
        model = UsuarioPersonalizado
        fields = ['username', 'email', 'password1', 'password2']


class CrearViajeForm(forms.ModelForm):
    """
       Formulario para crear un nuevo viaje.

       Permite a los usuarios crear viajes especificando destino personalizado,
       fechas y categoría. El destino se crea automáticamente si no existe.

       Campos adicionales:
           - destino_nombre: Campo libre para escribir "Ciudad, País"
           - categoria_destino: Tipo de destino (playa, montaña, ciudad, etc.)
    """
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
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AgregarActividadForm(forms.ModelForm):
    """
    Formulario para agregar actividades a un viaje.

    Permite definir todos los detalles de una actividad: horarios,
    ubicación, prioridad, categoría y coste estimado.

    Campos:
        - titulo: Nombre de la actividad
        - descripcion: Descripción detallada
        - fecha_hora: Fecha y hora programada (datetime-local)
        - ubicacion: Lugar donde se realizará
        - prioridad: Nivel de importancia (alta, media, baja)
        - categoria: Tipo de actividad (turismo, comida, transporte, etc.)
        - coste_estimado: Precio aproximado en euros

    Widgets especiales:
        - datetime-local: Para selección de fecha y hora
        - textarea: Para descripciones largas
        - number input: Para costes con decimales
    """
    class Meta:
        model = Actividad
        fields = ['titulo', 'descripcion', 'fecha_hora', 'ubicacion', 'prioridad', 'categoria', 'coste_estimado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'coste_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class EditarViajeForm(forms.ModelForm):
    """
    Formulario para editar viajes existentes.

    Permite modificar todos los aspectos de un viaje: destino, fechas,
    estado, visibilidad y imagen. Solo disponible para el creador del viaje
    o administradores.

    Campos:
        - nombre: Nombre del viaje
        - destino: Destino del viaje (selector de destinos existentes)
        - fecha_inicio/fecha_fin: Fechas del viaje
        - estado: Estado actual (planificado, en_curso, completado, cancelado)
        - visibilidad: Quién puede ver el viaje (publico, privado, amigos)
        - imagen: Imagen representativa del viaje
    """
    class Meta:
        model = Viaje
        fields = ['nombre', 'destino', 'fecha_inicio', 'fecha_fin', 'estado', 'visibilidad', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'destino': forms.Select(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'},format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'},format='%Y-%m-%d'),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'visibilidad': forms.Select(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

class FotoPerfilForm(forms.ModelForm):
    """
    Formulario para actualizar la foto de perfil del usuario.

    Permite subir imágenes para el avatar del usuario con preview automático
    mediante JavaScript. Solo acepta archivos de imagen.
    """
    class Meta:
        model = UsuarioPersonalizado
        fields = ['foto_perfil']
        widgets = {
            'foto_perfil': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'onchange': 'previewImage(this)'
            })
        }

class CambiarUsernameForm(forms.ModelForm):
    """
    Formulario para cambiar el nombre de usuario.

    Permite a los usuarios actualizar su username manteniendo
    la validación de unicidad de Django.

    Validaciones automáticas:
        - Nombre de usuario único en la base de datos
        - Longitud mínima y máxima según modelo
        - Caracteres permitidos (alfanuméricos y algunos símbolos)
    """
    class Meta:
        model = UsuarioPersonalizado
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'username': 'Nuevo nombre de usuario'
        }

class CambiarPasswordForm(PasswordChangeForm):
    """
    Formulario para cambiar la contraseña del usuario.

    Extiende el PasswordChangeForm de Django para aplicar estilos
    Bootstrap y mantener la validación de seguridad estándar.

    Campos:
        - old_password: Contraseña actual (verificación de seguridad)
        - new_password1: Nueva contraseña
        - new_password2: Confirmación de nueva contraseña

    Validaciones automáticas:
        - Verificación de contraseña actual
        - Complejidad de nueva contraseña (configurada en settings)
        - Coincidencia entre nueva contraseña y confirmación
        - No reutilización de contraseñas anteriores
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})
