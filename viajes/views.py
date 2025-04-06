from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView
from viajes.forms import RegistroUsuarioForm
from viajes.models import UsuarioPersonalizado

class IndexView(TemplateView):
    template_name = 'viajes/index.html'


class RegistroUsuarioView(CreateView):
    template_name = 'viajes/registro.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('viajes:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
        return response

class UsuarioLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        error = 'Usuario y/o contraseña incorrecto. Pruebe de nuevo.'
        return self.render_to_response(self.get_context_data(form=form, error=error))

class UsuarioLogoutView(LogoutView):
    template_name = 'registration/logged_out.html'


class PaginaInicioUsuarioView(TemplateView):
    template_name = 'viajes/pagina_inicio.html'
