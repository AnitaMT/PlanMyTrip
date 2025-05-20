import json
import random
import urllib.request, urllib.parse
from collections import defaultdict
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView, ListView
from viajes.forms import RegistroUsuarioForm, CrearViajeForm, AgregarActividadForm, EditarViajeForm, FotoPerfilForm, \
    CambiarUsernameForm, CambiarPasswordForm
from viajes.models import UsuarioPersonalizado, Viaje, Destino, Notificacion, Actividad, Gasto, DivisionGasto, MeGusta, \
    SolicitudAmistad


class IndexView(TemplateView):
    template_name = 'viajes/index.html'


class RegistroUsuarioView(CreateView):
    template_name = 'viajes/registro.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('viajes:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '¡Registro exitoso! Ahora puedes iniciar sesión.', extra_tags='registro')
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
        context['amigos'] = self.request.user.amigos.all()

        viajes_creados_activos = Viaje.objects.filter(creador=usuario, estado='ACTIVO')
        viajes_creados_finalizados = Viaje.objects.filter(creador=usuario, estado='FINALIZADO')

        viajes_colaborando_activos = Viaje.objects.filter(colaboradores=usuario, estado='ACTIVO')
        viajes_colaborando_finalizados = Viaje.objects.filter(colaboradores=usuario, estado='FINALIZADO')

        context['viajes_activos'] = (viajes_creados_activos | viajes_colaborando_activos).distinct()
        context['viajes_finalizados'] = (viajes_creados_finalizados | viajes_colaborando_finalizados).distinct()

        context['notificaciones_sin_leer_count'] = Notificacion.objects.filter(usuario=usuario, leido=False).count()
        context['ultimas_notificaciones'] = Notificacion.objects.filter(usuario=usuario).order_by('-fecha_creacion')[:5]
        context['solicitudes_pendientes_count'] = (self.request.user.solicitudes_recibidas.filter(aceptada__isnull=True).count())

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
        viaje = self.object
        user = self.request.user
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

        context['amigos'] = user.amigos.all()
        context['es_creador'] = (viaje.creador == user)

        context['deudas_agrupadas'] = obtener_deudas_agrupadas(viaje)

        context['deudas_detalladas'] = calcular_deudas(self.request, viaje.id)

        me_gustas = user.me_gustas_dados.filter(actividad__viaje=viaje)
        context['liked_actividades'] = [like.actividad.id for like in me_gustas]

        gastos_por_categoria = (Gasto.objects.filter(viaje=viaje).values('categoria').annotate(total=Sum('cantidad')))

        context['categorias'] = [g['categoria'] for g in gastos_por_categoria]
        context['cantidades'] = [float(g['total']) for g in gastos_por_categoria]

        ciudad = viaje.destino.nombre
        pais = viaje.destino.pais
        try:
            context['sugerencias'] = fetch_sugerencias_overpass(ciudad, pais)
        except Exception:
            context['sugerencias'] = []

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


class EnviarSolicitudView(LoginRequiredMixin, View):
    def post(self, request, pk):
        receptor = get_object_or_404(UsuarioPersonalizado, pk=pk)

        if receptor == request.user:
            return redirect('viajes:lista_amigos')

        solicitud, creada = SolicitudAmistad.objects.get_or_create(emisor=request.user, receptor=receptor)

        if creada:
            mensaje = f'{request.user.username} te ha enviado solicitud de amistad.'
            enlace = reverse('viajes:solicitudes_recibidas')
            Notificacion.objects.create(usuario=receptor, mensaje=mensaje, tipo='SOLICITUD_AMISTAD', enlace_relacionado=enlace)

        return redirect('viajes:inicio')

class UsuariosDisponiblesView(LoginRequiredMixin, ListView):
    model = UsuarioPersonalizado
    template_name = 'viajes/usuarios_disponibles.html'
    context_object_name = 'usuarios'

    def get_queryset(self):
        usuario = self.request.user
        amigos = usuario.amigos.all()
        return UsuarioPersonalizado.objects.exclude(pk__in=amigos).exclude(pk=usuario.pk)


class ListaSolicitudesView(LoginRequiredMixin, ListView):
    template_name = 'viajes/solicitudes_recibidas.html'
    context_object_name = 'solicitudes'

    def get_queryset(self):
        return self.request.user.solicitudes_recibidas.filter(aceptada__isnull=True)


class ResponderSolicitudView(LoginRequiredMixin, View):
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudAmistad, pk=pk, receptor=request.user)
        accion = request.POST['accion']
        solicitud.aceptada = (accion == 'aceptada')
        solicitud.save()

        if solicitud.aceptada:
            request.user.amigos.add(solicitud.emisor)
            mensaje = f"{request.user.username} ha aceptado tu solicitud de amistad."
            enlace = reverse('viajes:lista_amigos')
            Notificacion.objects.create(usuario=solicitud.emisor, mensaje=mensaje, tipo='SOLICITUD_ACEPTADA', enlace_relacionado=enlace)

        return redirect('viajes:solicitudes_recibidas')


class ListaAmigosView(LoginRequiredMixin, ListView):
    template_name = 'viajes/lista_amigos.html'
    context_object_name = 'amigos'

    def get_queryset(self):
        return self.request.user.amigos.all()


class EliminarAmigoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        amigo = get_object_or_404(UsuarioPersonalizado, pk=pk)

        # Verificar que el usuario es realmente amigo
        if amigo in request.user.amigos.all():
            request.user.amigos.remove(amigo)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Este usuario no es tu amigo'}, status=400)

class AgregarColaboradorView(LoginRequiredMixin, View):
    def post(self, request, viaje_id):
        try:
            data = json.loads(request.body)
            usuario_id = data.get('usuario_id')

            if not usuario_id:
                return JsonResponse({'success': False, 'error': 'Usuario no seleccionado'}, status=400)

            viaje = get_object_or_404(Viaje, id=viaje_id, creador=request.user)
            usuario = get_object_or_404(UsuarioPersonalizado, pk=usuario_id)

            if not request.user.amigos.filter(pk=usuario.pk).exists():
                return JsonResponse({'success': False, 'error': 'Ese usuario no es tu amigo'}, status=400)

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

            mensaje = f"Has sido añadido al viaje '{viaje.nombre}' por: {request.user.username}"
            enlace = reverse('viajes:detalles_viaje', kwargs={'pk': viaje.id})

            Notificacion.objects.create(usuario=usuario, mensaje=mensaje, tipo='COLABORADOR', enlace_relacionado=enlace)

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

    divisiones_pendientes = DivisionGasto.objects.filter(gasto__viaje=viaje,pagado=False).select_related('gasto__pagador', 'deudor')

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
    paginate_by = 5

    def get_queryset(self):
        self.viaje = get_object_or_404(Viaje, pk=self.kwargs['pk'])
        return Gasto.objects.filter(viaje=self.viaje).order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viaje = self.viaje

        context['deudas_agrupadas'] = obtener_deudas_agrupadas(viaje)

        context['deudas_detalladas'] = calcular_deudas(self.request, viaje.id)

        context['viaje'] = viaje
        gastos_deudores = {}
        for gasto in context['gastos']:
            lista = [
                div.deudor.username
                for div in gasto.divisiones.all()
                if div.deudor != gasto.pagador
            ]
            gastos_deudores[gasto.id] = lista
        context['gastos_deudores'] = gastos_deudores

        return context

def obtener_deudas_agrupadas(viaje):
    qs = DivisionGasto.objects.filter(gasto__viaje=viaje, pagado=False).exclude(deudor=F('gasto__pagador'))

    return (qs.values('deudor', 'deudor__username', 'gasto__pagador', 'gasto__pagador__username',).annotate(total_deuda=Sum('cantidad_a_pagar')))


class EliminarGastoView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        gasto = get_object_or_404(Gasto, pk=pk)

        if gasto.pagador != request.user and gasto.viaje.creador != request.user:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para eliminar este gasto'
            }, status=403)

        viaje = gasto.viaje
        participantes = viaje.colaboradores.all() | UsuarioPersonalizado.objects.filter(pk=viaje.creador.pk)
        participantes = participantes.distinct().exclude(pk=request.user.pk)

        mensaje = f"{request.user.username} eliminó un gasto de {gasto.cantidad}€ ({gasto.descripcion})"
        enlace = reverse('viajes:detalles_viaje', kwargs={'pk': viaje.pk})
        for participante in participantes:
            Notificacion.objects.create(usuario=participante, mensaje=mensaje, tipo='GASTO', enlace_relacionado=enlace)

        gasto.delete()

        return JsonResponse({'success': True})

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
        usuarios = actividad.me_gustas.select_related('usuario').all()
        data = {
            'usuarios': [
                {
                    'username': mg.usuario.username,
                    'foto_perfil': mg.usuario.foto_perfil.url if mg.usuario.foto_perfil else None
                }
                for mg in usuarios
            ]
        }
        return JsonResponse(data)


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

class NotificacionListView(LoginRequiredMixin, TemplateView):
    template_name = 'viajes/notificaciones.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        todas_notificaciones = Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')
        paginator = Paginator(todas_notificaciones, 10)
        page = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page)

        return context

class MarcarTodasLeidasView(LoginRequiredMixin, View):
    def post(self, request):
        Notificacion.objects.filter(usuario=self.request.user, leido=False).update(leido=True)

        return redirect('viajes:notificaciones')


class EliminarNotificacionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        notificacion_id = self.kwargs.get('pk')
        notificacion = get_object_or_404(Notificacion, pk=notificacion_id)
        notificacion.delete()

        return JsonResponse({'success': True})

def fetch_sugerencias_overpass(ciudad, pais, limite=5):
    """
    1. Usa Nominatim para obtener lat/lon de la ciudad.
    2. Consulta Overpass buscando puntos de interés.
    3. Elimina hostels, guest_houses, hoteles y sin nombre.
    4. Devuelve lista de strings "Nombre (tipo)" aleatoria.
    """
    # Geocodificar con Nominatim (es el geocodificador de OpenStreetMap)
    nominatim_url = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&q=' + urllib.parse.quote(f"{ciudad}, {pais}")
    with urllib.request.urlopen(nominatim_url) as resp:
        results = json.loads(resp.read().decode())
    if not results:
        return []
    lat = results[0]['lat']
    lon = results[0]['lon']

    # Query Overpass around 10km radius
    query = f'''[out:json][timeout:25];
    (
      node["tourism"](around:10000,{lat},{lon});
      way["tourism"](around:10000,{lat},{lon});
      rel["tourism"](around:10000,{lat},{lon});
    );
    out center;'''
    url = 'https://overpass-api.de/api/interpreter?data=' + urllib.parse.quote(query)
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
    elementos = data.get('elements', [])

    # Filtro resultados: excluir tipos no deseados y sin nombre
    excluir = {'hostel', 'guest_house', 'hotel', 'camp_site', 'apartment', 'caravan_site'}
    filtrados = []
    for el in elementos:
        tags = el.get('tags', {})
        tipo = tags.get('tourism')
        nombre = tags.get('name')
        if not nombre or tipo in excluir:
            continue
        filtrados.append(el)

    # Mezclo y formato
    random.shuffle(filtrados)
    sugerencias = []
    for el in filtrados[:limite]:
        tags = el.get('tags', {})
        nombre = tags.get('name')
        tipo = tags.get('tourism', tags.get('historic', 'Desconocido'))
        sugerencias.append(f"{nombre} ({tipo})")

    return sugerencias

