import json
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView
from viajes.forms import RegistroUsuarioForm, CrearViajeForm, AgregarActividadForm
from viajes.models import UsuarioPersonalizado, Viaje, Destino, Notificacion, Actividad


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


class AgregarColaboradorView(LoginRequiredMixin, View):
    def post(self, request, viaje_id):
        try:
            data = json.loads(request.body)
            username_input = data.get('username', '').strip()

            if not username_input:
                return JsonResponse({'success': False, 'error': 'Nombre de usuario no proporcionado'}, status=400)

            viaje = get_object_or_404(Viaje, id=viaje_id, creador=request.user)
            usuario = UsuarioPersonalizado.objects.filter(username__iexact=username_input).first()

            if not usuario:
                return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)

            if usuario == request.user:
                return JsonResponse({'success': False, 'error': 'No puedes añadirte a ti mismo'}, status=400)

            if viaje.colaboradores.filter(id=usuario.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'El usuario {usuario.username} ya es colaborador de este viaje'
                }, status=400)

            viaje.colaboradores.add(usuario)

            return JsonResponse({
                'success': True,
                'username': usuario.username,
                'id': usuario.id,
                'viaje_id': viaje.id
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

class EliminarColaboradorView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        colaborador_id = self.kwargs.get('pk')
        colaborador = get_object_or_404(UsuarioPersonalizado, pk=colaborador_id)

        viaje_id = self.kwargs.get('viaje_id')
        viaje = get_object_or_404(Viaje, id=viaje_id, creador=request.user)

        viaje.colaboradores.remove(colaborador)

        return JsonResponse({'success': True})

class AgregarActividadView(LoginRequiredMixin, CreateView):
    model = Actividad
    form_class = AgregarActividadForm
    template_name = 'viajes/agregar_actividad.html'

    def form_valid(self, form):
        actividad = form.save(commit=False)
        actividad.creador = self.request.user
        viaje_id = self.kwargs.get('pk')
        actividad.viaje = get_object_or_404(Viaje, pk=viaje_id)
        actividad.save()
        messages.success(self.request, 'Actividad agregada con éxito')

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viajes:detalles_viaje', kwargs={'pk': self.kwargs.get('pk')})

class DetallesActividadView(LoginRequiredMixin, TemplateView):
    template_name = 'viajes/detalles_actividad.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = get_object_or_404(Actividad, pk=self.kwargs['pk'])
        context['actividad'] = actividad
        return context

class EditarActividadView(LoginRequiredMixin, UpdateView):
    model = Actividad
    form_class = AgregarActividadForm
    template_name = 'viajes/agregar_actividad.html'

    def get_queryset(self):
        return Actividad.objects.filter(creador=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada con exito')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viajes:detalles_viaje', kwargs={'pk': self.object.viaje.pk})


class EliminarActividadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        actividad_id = self.kwargs.get('pk')
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        actividad.delete()

        return JsonResponse({'success': True})