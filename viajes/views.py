import json
from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView, ListView
from viajes.forms import RegistroUsuarioForm, CrearViajeForm, AgregarActividadForm, EditarViajeForm, FotoPerfilForm, \
    CambiarUsernameForm, CambiarPasswordForm
from viajes.models import UsuarioPersonalizado, Viaje, Destino, Notificacion, Actividad, Gasto, DivisionGasto, MeGusta


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

        viajes_creados_activos = Viaje.objects.filter(creador=usuario, estado='ACTIVO')
        viajes_creados_finalizados = Viaje.objects.filter(creador=usuario, estado='FINALIZADO')

        viajes_colaborando_activos = Viaje.objects.filter(colaboradores=usuario, estado='ACTIVO')
        viajes_colaborando_finalizados = Viaje.objects.filter(colaboradores=usuario, estado='FINALIZADO')

        context['viajes_activos'] = (viajes_creados_activos | viajes_colaborando_activos).distinct()
        context['viajes_finalizados'] = (viajes_creados_finalizados | viajes_colaborando_finalizados).distinct()

        context['notificaciones_sin_leer_count'] = Notificacion.objects.filter(usuario=usuario, leido=False).count()
        context['ultimas_notificaciones'] = Notificacion.objects.filter(usuario=usuario).order_by('-fecha_creacion')[:5]

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
        user = self.request.user
        viaje = self.object
        deudas = calcular_deudas(self.request, viaje.id)
        deudas_resumen = {}

        for deudor, deudas_lista in deudas.items():
            total = Decimal('0.00')

            for deuda_info in deudas_lista:
                cantidad = deuda_info['deuda']
                total += cantidad

            deudas_resumen[deudor.username] = round(Decimal(total), 2)

        context['deudas'] = deudas_resumen
        context['deudas_detalladas'] = deudas

        context['es_creador'] = viaje.creador == self.request.user

        me_gustas_del_usuario = user.me_gustas_dados.all()

        likes_del_viaje = me_gustas_del_usuario.filter(actividad__viaje=viaje)

        ids_de_actividades = [like.actividad.id for like in likes_del_viaje]

        context['liked_actividades'] = list(ids_de_actividades)

        return context

class EditarViajeView(LoginRequiredMixin, UpdateView):
    model = Viaje
    form_class = EditarViajeForm
    template_name = 'viajes/editar_viaje.html'

    def form_valid(self, form):
        messages.success(self.request, 'Viaje actualizado con exito')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viajes:detalles_viaje', kwargs={'pk': self.object.pk})



class EliminarViajeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        viaje_id = self.kwargs['pk']
        viaje = get_object_or_404(Viaje, pk=viaje_id)

        viaje.delete()

        return JsonResponse({'success': True})



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

        viaje = actividad.viaje
        usuarios_a_notificar = list(viaje.colaboradores.all()) + [viaje.creador]
        usuarios_a_notificar = [u for u in set(usuarios_a_notificar) if u != self.request.user]

        mensaje = f"{self.request.user.username} ha añadido la actividad: {actividad.titulo}"
        enlace = reverse('viajes:detalles_viaje', kwargs={'pk': viaje.pk})

        for u in usuarios_a_notificar:
            Notificacion.objects.create(usuario=u, mensaje=mensaje, tipo='ACTIVIDAD', enlace_relacionado=enlace)

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

    def form_valid(self, form):
        actividad = form.save()
        viaje = actividad.viaje
        usuarios_a_notificar = list(viaje.colaboradores.all()) + [viaje.creador]
        usuarios_a_notificar = [u for u in set(usuarios_a_notificar) if u != self.request.user]
        mensaje = f"{self.request.user.username} modificó la actividad: {actividad.titulo}"
        enlace = reverse('viajes:detalles_viaje', kwargs={'pk': viaje.pk})

        for u in usuarios_a_notificar:
            Notificacion.objects.create(usuario=u, mensaje=mensaje, tipo='ACTIVIDAD', enlace_relacionado=enlace)

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


class AgregarGastoView(LoginRequiredMixin, CreateView):
    model = Gasto
    fields = ['cantidad', 'descripcion', 'categoria', 'comprobante']
    template_name = 'viajes/agregar_gasto.html'

    def form_valid(self, form):
        viaje = get_object_or_404(Viaje, pk=self.kwargs['pk'])
        gasto = form.save(commit=False)
        gasto.viaje = viaje
        gasto.pagador = self.request.user
        gasto.save()

        participantes_ids = self.request.POST.getlist('participantes', None)

        if participantes_ids:
            participantes = UsuarioPersonalizado.objects.filter(id__in=participantes_ids)
        else:
            participantes = [viaje.creador] + list(viaje.colaboradores.all())

        cantidad_por_persona = gasto.cantidad / len(participantes)

        for participante in participantes:
            DivisionGasto.objects.create(
                gasto=gasto,
                deudor=participante,
                cantidad_a_pagar=cantidad_por_persona,
                pagado=(participante == self.request.user)
            )

        participantes = viaje.colaboradores.all() | UsuarioPersonalizado.objects.filter(pk=viaje.creador.pk)
        participantes = participantes.distinct().exclude(pk=self.request.user.pk)
        mensaje = f"{self.request.user.username} registró un gasto de {gasto.cantidad}€ en '{gasto.descripcion}'"
        enlace = reverse('viajes:detalles_viaje', kwargs={'pk': viaje.pk})

        for participante in participantes:
            Notificacion.objects.create(usuario=participante, mensaje=mensaje, tipo='GASTO', enlace_relacionado=enlace)

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '¡Gasto registrado correctamente!'
            })


        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({
                'success': False,
                'error': 'Error en el formulario',
                'errors': errors
            }, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('viajes:detalles_viaje', kwargs={'pk': self.kwargs['pk']})

def calcular_deudas(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    deudas = defaultdict(list)

    divisiones_pendientes = DivisionGasto.objects.filter(
        gasto__viaje=viaje,
        pagado=False
    ).select_related('gasto__pagador', 'deudor')

    for division in divisiones_pendientes:
        if division.deudor != division.gasto.pagador:
            deudas[division.deudor].append({
                'deudor': division.deudor,
                'pagador': division.gasto.pagador,
                'deuda': round(division.cantidad_a_pagar, 2)
            })

    return dict(deudas)

class ListaGastosView(LoginRequiredMixin, ListView):
    model = Gasto
    template_name = 'viajes/lista_gastos.html'
    context_object_name = 'gastos'

    def get_queryset(self):
        self.viaje = get_object_or_404(Viaje, pk=self.kwargs['pk'])
        return Gasto.objects.filter(viaje=self.viaje).order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['viaje'] = self.viaje
        context['deudas'] = calcular_deudas(self.request, self.viaje.id)
        context['deudas_con_deudores'] = context['deudas']

        gastos_deudores = {}

        for gasto in context['gastos']:
            todas_las_divisiones = DivisionGasto.objects.filter(gasto=gasto)

            lista_deudores = []

            for division in todas_las_divisiones:
                if division.deudor != gasto.pagador:
                    lista_deudores.append(division.deudor.username)

            gastos_deudores[gasto.id] = lista_deudores

        context['gastos_deudores'] = gastos_deudores

        return context

class LikeToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        actividad = get_object_or_404(Actividad, pk=pk)
        usuario = request.user

        like_obj, created = MeGusta.objects.get_or_create(actividad=actividad, usuario=usuario)

        if created and actividad.creador != usuario:
            mensaje = f"A {usuario.username} le gustó tu actividad: {actividad.titulo}"
            enlace = reverse('viajes:detalles_actividad', kwargs={'pk': actividad.pk})

            Notificacion.objects.create(usuario=actividad.creador, mensaje=mensaje, tipo='OTROS', enlace_relacionado=enlace)

            liked = True
        else:
            if not created:
                like_obj.delete()
            liked = False


        total = actividad.me_gustas.count()

        return JsonResponse({'liked': liked, 'count': total})

class ActividadLikesView(LoginRequiredMixin, View):
    def get(self, request, pk):
        actividad = get_object_or_404(Actividad, pk=pk)
        usernames = actividad.me_gustas.values_list('usuario__username', flat=True)
        return JsonResponse({'usuarios': list(usernames)})


class AjustesUsuarioView(LoginRequiredMixin, TemplateView):
    template_name = 'viajes/ajustes_usuario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['foto_form'] = FotoPerfilForm(instance=self.request.user)
        context['username_form'] = CambiarUsernameForm(instance=self.request.user)
        context['password_form'] = CambiarPasswordForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        if 'foto_submit' in request.POST:
            return self.procesar_foto_perfil(request)
        elif 'username_submit' in request.POST:
            return self.procesar_username(request)
        elif 'password_submit' in request.POST:
            return self.procesar_password(request)
        return redirect('viajes:ajustes_usuario')

    def procesar_foto_perfil(self, request):
        form = FotoPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto de perfil actualizada correctamente')
        return redirect('viajes:ajustes_usuario')

    def procesar_username(self, request):
        form = CambiarUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nombre de usuario actualizado correctamente')
        return redirect('viajes:ajustes_usuario')

    def procesar_password(self, request):
        form = CambiarPasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña cambiada correctamente')
        return redirect('viajes:ajustes_usuario')

class NotificacionRedirectView(LoginRequiredMixin, View):
    def get(self, request, pk):
        notificacion = get_object_or_404(Notificacion, pk=pk, usuario=self.request.user)
        notificacion.leido = True
        notificacion.save(update_fields=['leido'])

        destino = notificacion.enlace_relacionado or reverse('viajes:inicio')

        return redirect(destino)
