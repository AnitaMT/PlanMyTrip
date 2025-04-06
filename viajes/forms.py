from django import forms
from django.contrib.auth.forms import UserCreationForm

from viajes.models import UsuarioPersonalizado


class RegistroUsuarioForm(UserCreationForm):
    class Meta:
        model = UsuarioPersonalizado
        fields = ['username', 'email', 'password1', 'password2']