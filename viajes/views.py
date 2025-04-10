from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, DetailView
from viajes.forms import RegistroUsuarioForm, CrearViajeForm
from viajes.models import UsuarioPersonalizado, Viaje, Destino, Notificacion


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


class PaginaInicioUsuarioView(LoginRequiredMixin, TemplateView):
    template_name = 'viajes/pagina_inicio.html'
    success_url = reverse_lazy('viajes:inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario = self.request.user
        context['viajes_activos'] = Viaje.objects.filter(creador=usuario, estado='ACTIVO')
        context['viajes_finalizados'] = Viaje.objects.filter(creador=usuario, estado='FINALIZADO')
        context['notificaciones_sin_leer_count'] = Notificacion.objects.filter(usuario=usuario, leido=False).count()

        return context


class CrearViajeView(LoginRequiredMixin, CreateView):
    model = Viaje
    form_class = CrearViajeForm
    template_name = 'viajes/crear_viaje.html'
    success_url = reverse_lazy('viajes:inicio')

    def form_valid(self, form):
        destino_str = form.cleaned_data['destino_nombre']
        partes = [p.strip() for p in destino_str.split(',')]

        nombre = partes[0]
        pais = partes[1] if len(partes) > 1 else 'Desconocido'

        destino, created = Destino.objects.get_or_create(
            nombre=nombre,
            pais=pais,
            defaults={
                'categoria': form.cleaned_data['categoria_destino'],
                'descripcion': f"Destino creado automáticamente para el viaje {form.cleaned_data['nombre']}"
            }
        )

        viaje = form.save(commit=False)
        viaje.creador = self.request.user
        viaje.destino = destino
        viaje.save()

        if created:
            messages.info(self.request, f"Se creó un nuevo destino: {destino.nombre}")

        return super().form_valid(form)

class DetallesViajeView(LoginRequiredMixin, DetailView):
    model = Viaje
    template_name = 'viajes/detalles_viaje.html'
    context_object_name = 'viaje'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
