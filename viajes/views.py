import json
import random
import requests
import urllib.request, urllib.parse
from collections import defaultdict
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Q, Count
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView, ListView
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from viajes.forms import RegistroUsuarioForm, CrearViajeForm, AgregarActividadForm, EditarViajeForm, FotoPerfilForm, \
    CambiarUsernameForm, CambiarPasswordForm
from viajes.models import UsuarioPersonalizado, Viaje, Destino, Notificacion, Actividad, Gasto, DivisionGasto, MeGusta, \
    SolicitudAmistad


class IndexView(TemplateView):
    """
    Muestra la página principal de bienvenida de PlanMyTrip.
    Es la primera página que ven los usuarios cuando entran a la aplicación.
    """
    template_name = 'viajes/index.html'


class RegistroUsuarioView(CreateView):
    """
    Permite a nuevos usuarios registrarse en la aplicación.
    Muestra un formulario de registro y crea una nueva cuenta de usuario.
    Cuando el registro es exitoso, redirige al login con un mensaje de confirmación.
    """
    template_name = 'viajes/registro.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('viajes:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '¡Registro exitoso! Ahora puedes iniciar sesión.', extra_tags='registro')
        return response


class UsuarioLoginView(LoginView):
    """
    Permite a nuevos usuarios registrarse en la aplicación.
    Muestra un formulario de registro y crea una nueva cuenta de usuario.
    Cuando el registro es exitoso, redirige al login con un mensaje de confirmación.
    """
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        error = 'Usuario y/o contraseña incorrecto. Pruebe de nuevo.'
        return self.render_to_response(self.get_context_data(form=form, error=error))


class UsuarioLogoutView(LogoutView):
    """
    Cierra la sesión del usuario y lo redirige a una página de despedida.
    """
    template_name = 'registration/logged_out.html'


class PaginaInicioUsuarioView(LoginRequiredMixin, TemplateView):
    """
    Página principal del usuario logueado, como su dashboard personal.
    Muestra todos sus viajes (activos y finalizados), notificaciones sin leer,
    solicitudes de amistad pendientes y la lista de sus amigos.
    """
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
    """
    Permite al usuario crear un nuevo viaje.
    Procesa automáticamente el destino introducido y crea uno nuevo si no existe.
    Soporta tanto formularios normales como peticiones AJAX para una mejor experiencia de usuario.
    """
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

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '¡Viaje creado correctamente!'
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


class DetallesViajeView(LoginRequiredMixin, DetailView):
    """
    Muestra toda la información detallada de un viaje específico.
    Incluye actividades, gastos, deudas entre participantes, colaboradores,
    gráficos de gastos por categoría y sugerencias de actividades usando IA.
    También muestra quién le ha dado like a las actividades del viaje.
    """
    model = Viaje
    template_name = 'viajes/detalles_viaje.html'
    context_object_name = 'viaje'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viaje = self.object
        usuario = self.request.user
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

        context['amigos'] = usuario.amigos.all()
        context['es_creador'] = (viaje.creador == usuario)
        context['es_colaborador'] = usuario in viaje.colaboradores.all()

        context['deudas_agrupadas'] = obtener_deudas_agrupadas(viaje)

        context['deudas_detalladas'] = calcular_deudas(self.request, viaje.id)

        me_gustas = usuario.me_gustas_dados.filter(actividad__viaje=viaje)
        context['liked_actividades'] = [like.actividad.id for like in me_gustas]

        gastos_por_categoria = (Gasto.objects.filter(viaje=viaje).values('categoria').annotate(total=Sum('cantidad')))

        context['categorias'] = [g['categoria'] for g in gastos_por_categoria]
        context['cantidades'] = [float(g['total']) for g in gastos_por_categoria]

        context['notificaciones_sin_leer_count'] = Notificacion.objects.filter(usuario=usuario, leido=False).count()
        context['ultimas_notificaciones'] = Notificacion.objects.filter(usuario=usuario).order_by('-fecha_creacion')[:5]
        context['solicitudes_pendientes_count'] = (self.request.user.solicitudes_recibidas.filter(aceptada__isnull=True).count())

        ciudad = viaje.destino.nombre
        pais = viaje.destino.pais

        try:
            sugerencias_ia = fetch_sugerencias_gemini(ciudad, pais, limite=5)
        except Exception:
            sugerencias_ia = []

        if sugerencias_ia:
            context['sugerencias'] = sugerencias_ia
        else:
            try:
                context['sugerencias'] = fetch_sugerencias_overpass(ciudad, pais)
            except Exception:
                context['sugerencias'] = []

        return context


class EditarViajeView(LoginRequiredMixin, UpdateView):
    """
    Permite al creador del viaje modificar los detalles básicos del viaje,
    como nombre, fechas, descripción, etc.
    """
    model = Viaje
    form_class = EditarViajeForm
    template_name = 'viajes/editar_viaje.html'

    def form_valid(self, form):
        messages.success(self.request, 'Viaje actualizado con exito')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viajes:detalles_viaje', kwargs={'pk': self.object.pk})



class EliminarViajeView(LoginRequiredMixin, View):
    """
    Elimina completamente un viaje de la base de datos.
    Solo el creador del viaje puede eliminarlo.
    Responde con JSON para peticiones AJAX.
    """
    def post(self, request, *args, **kwargs):
        viaje_id = self.kwargs['pk']
        viaje = get_object_or_404(Viaje, pk=viaje_id)

        viaje.delete()

        return JsonResponse({'success': True})


class EnviarSolicitudView(LoginRequiredMixin, View):
    """
    Envía una solicitud de amistad a otro usuario.
    Verifica que no exista ya una solicitud pendiente y crea una notificación
    para informar al receptor de la nueva solicitud.
    """
    def post(self, request, pk):
        receptor = get_object_or_404(UsuarioPersonalizado, pk=pk)

        if receptor == request.user:
            return redirect('viajes:lista_amigos')

        solicitud_existente = SolicitudAmistad.objects.filter(emisor=request.user, receptor=receptor,aceptada__isnull=True).first()

        if not solicitud_existente:
            SolicitudAmistad.objects.filter(emisor=request.user, receptor=receptor).delete()

            solicitud = SolicitudAmistad.objects.create(emisor=request.user, receptor=receptor)

            mensaje = f'{request.user.username} te ha enviado solicitud de amistad.'
            enlace = reverse('viajes:solicitudes_recibidas')
            Notificacion.objects.create(usuario=receptor, mensaje=mensaje, tipo='SOLICITUD_AMISTAD', enlace_relacionado=enlace)

        return redirect('viajes:inicio')

class UsuariosDisponiblesView(LoginRequiredMixin, ListView):
    """
    Muestra una lista de todos los usuarios que aún no son amigos del usuario actual.
    Útil para encontrar nuevos usuarios y enviarles solicitudes de amistad.
    """
    model = UsuarioPersonalizado
    template_name = 'viajes/usuarios_disponibles.html'
    context_object_name = 'usuarios'

    def get_queryset(self):
        usuario = self.request.user
        amigos = usuario.amigos.all()
        return UsuarioPersonalizado.objects.exclude(pk__in=amigos).exclude(pk=usuario.pk)


class ListaSolicitudesView(LoginRequiredMixin, ListView):
    """
    Muestra todas las solicitudes de amistad que el usuario ha recibido
    y que aún están pendientes de respuesta (aceptar o rechazar).
    """
    template_name = 'viajes/solicitudes_recibidas.html'
    context_object_name = 'solicitudes'

    def get_queryset(self):
        return self.request.user.solicitudes_recibidas.filter(aceptada__isnull=True)


class ResponderSolicitudView(LoginRequiredMixin, View):
    """
    Permite aceptar o rechazar una solicitud de amistad.
    Si se acepta, añade a ambos usuarios como amigos mutuamente
    y envía una notificación de confirmación al emisor.
    """
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
    """
    Muestra la lista de todos los amigos del usuario actual.
    Desde aquí se puede ver el perfil de cada amigo y eliminar amistades.
    """
    template_name = 'viajes/lista_amigos.html'
    context_object_name = 'amigos'

    def get_queryset(self):
        return self.request.user.amigos.all()


class EliminarAmigoView(LoginRequiredMixin, View):
    """
    Elimina una amistad entre el usuario actual y otro usuario.
    Verifica que realmente sean amigos antes de eliminar la relación.
    Responde con JSON para peticiones AJAX.
    """
    def post(self, request, pk):
        amigo = get_object_or_404(UsuarioPersonalizado, pk=pk)

        # Verificar que el usuario es realmente amigo
        if amigo in request.user.amigos.all():
            request.user.amigos.remove(amigo)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Este usuario no es tu amigo'}, status=400)

class AgregarColaboradorView(LoginRequiredMixin, View):
    """
    Añade un amigo como colaborador a un viaje específico.
    Solo el creador del viaje puede añadir colaboradores.
    Verifica que el usuario sea amigo antes de añadirlo y envía una notificación.
    """
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
    """
    Elimina a un colaborador de un viaje específico.
    Solo el creador del viaje puede eliminar colaboradores.
    Responde con JSON para peticiones AJAX.
    """
    def post(self, request, *args, **kwargs):
        colaborador_id = self.kwargs.get('pk')
        colaborador = get_object_or_404(UsuarioPersonalizado, pk=colaborador_id)

        viaje_id = self.kwargs.get('viaje_id')
        viaje = get_object_or_404(Viaje, id=viaje_id, creador=request.user)

        viaje.colaboradores.remove(colaborador)

        return JsonResponse({'success': True})


class AgregarActividadView(LoginRequiredMixin, CreateView):
    """
    Permite añadir una nueva actividad a un viaje existente.
    Notifica a todos los participantes del viaje sobre la nueva actividad.
    Soporta tanto formularios normales como peticiones AJAX.
    """
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

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '¡Actividad creada correctamente!'
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
        return reverse('viajes:detalles_viaje', kwargs={'pk': self.kwargs.get('pk')})


class DetallesActividadView(LoginRequiredMixin, TemplateView):
    """
    Muestra los detalles completos de una actividad específica,
    incluyendo descripción, fecha, hora, ubicación y coste estimado.
    """
    template_name = 'viajes/detalles_actividad.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = get_object_or_404(Actividad, pk=self.kwargs['pk'])
        context['actividad'] = actividad
        return context


class EditarActividadView(LoginRequiredMixin, UpdateView):
    """
    Permite modificar una actividad existente.
    Notifica a todos los participantes del viaje sobre la modificación.
    """
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
    """
    Elimina una actividad de un viaje.
    Solo el creador de la actividad o el creador del viaje pueden eliminarla.
    Responde con JSON para peticiones AJAX.
    """
    def post(self, request, *args, **kwargs):
        actividad_id = self.kwargs.get('pk')
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        actividad.delete()

        return JsonResponse({'success': True})


class AgregarGastoView(LoginRequiredMixin, CreateView):
    """
    Registra un nuevo gasto en un viaje y lo divide automáticamente
    entre los participantes seleccionados. Si no se seleccionan participantes,
    divide el gasto entre todos los miembros del viaje.
    Notifica a todos los participantes sobre el nuevo gasto.
    """
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
    """
    Función auxiliar que calcula todas las deudas pendientes de un viaje.
    Devuelve un diccionario con cada deudor y la lista de sus deudas pendientes,
    incluyendo a quién le debe y cuánto dinero.
    """
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
    """
    Muestra todos los gastos de un viaje específico en formato de lista paginada.
    Incluye información sobre las deudas entre participantes y quién debe dinero a quién.
    También muestra qué participantes están involucrados en cada gasto.
    """
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
    """
    Función auxiliar que agrupa las deudas por persona.
    Suma todas las deudas que una persona tiene con otra para mostrar
    un total consolidado en lugar de deudas individuales por gasto.
    """
    qs = DivisionGasto.objects.filter(gasto__viaje=viaje, pagado=False).exclude(deudor=F('gasto__pagador'))

    return (qs.values('deudor', 'deudor__username', 'gasto__pagador', 'gasto__pagador__username',).annotate(total_deuda=Sum('cantidad_a_pagar')))


class EliminarGastoView(LoginRequiredMixin, View):
    """
    Elimina un gasto específico del viaje.
    Solo el usuario que registró el gasto o el creador del viaje pueden eliminarlo.
    Notifica a todos los participantes sobre la eliminación.
    """
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
    """
    Vista que maneja cuando un usuario le da "me gusta" a una actividad.
    Si ya le había dado like, se lo quita. Si no tenía like, se lo pone.
    También envía una notificación al creador de la actividad (si no es el mismo usuario).
    Devuelve si quedó con like o sin like, y el total de likes que tiene la actividad.
    """
    def post(self, request, pk):
        actividad = get_object_or_404(Actividad, pk=pk)
        usuario = request.user

        like_obj, created = MeGusta.objects.get_or_create(actividad=actividad, usuario=usuario)

        if created:
            mensaje = f"A {usuario.username} le gustó tu actividad: {actividad.titulo}"
            enlace = reverse('viajes:detalles_actividad', kwargs={'pk': actividad.pk})

            if actividad.creador != usuario:
                Notificacion.objects.create(usuario=actividad.creador, mensaje=mensaje, tipo='OTROS', enlace_relacionado=enlace)

            liked = True
        else:
            if not created:
                like_obj.delete()
            liked = False

        total = actividad.me_gustas.count()

        return JsonResponse({'liked': liked, 'count': total})

class ActividadLikesView(LoginRequiredMixin, View):
    """
    Vista que devuelve la lista de usuarios que le han dado like a una actividad.
    Se usa para mostrar quién le gustó la actividad cuando haces clic en el contador de likes.
    Devuelve el nombre de usuario y la foto de perfil de cada persona.
    """
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
    """
    Vista de la página de ajustes del usuario donde puede cambiar:
    - Su foto de perfil
    - Su nombre de usuario
    - Su contraseña
    Maneja los tres formularios en la misma página y redirige según qué botón se presione.
    """
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
            messages.success(request, 'Foto de perfil actualizada correctamente', extra_tags='user_settings')
        return redirect('viajes:ajustes_usuario')

    def procesar_username(self, request):
        form = CambiarUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nombre de usuario actualizado correctamente', extra_tags='user_settings')
        return redirect('viajes:ajustes_usuario')

    def procesar_password(self, request):
        form = CambiarPasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña cambiada correctamente', extra_tags='user_settings')
        return redirect('viajes:ajustes_usuario')

class NotificacionRedirectView(LoginRequiredMixin, View):
    """
    Vista que se ejecuta cuando un usuario hace clic en una notificación.
    Marca la notificación como leída y redirige al usuario a la página relacionada
    (por ejemplo, al viaje o actividad que generó la notificación).
    """
    def get(self, request, pk):
        notificacion = get_object_or_404(Notificacion, pk=pk, usuario=self.request.user)
        notificacion.leido = True
        notificacion.save(update_fields=['leido'])

        destino = notificacion.enlace_relacionado or reverse('viajes:inicio')

        return redirect(destino)

class NotificacionListView(LoginRequiredMixin, TemplateView):
    """
    Vista que muestra todas las notificaciones del usuario en una lista paginada.
    Las notificaciones aparecen ordenadas por fecha (las más recientes primero).
    Muestra 10 notificaciones por página.
    """
    template_name = 'viajes/notificaciones.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        todas_notificaciones = Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')
        paginator = Paginator(todas_notificaciones, 10)
        page = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page)

        return context

class MarcarTodasLeidasView(LoginRequiredMixin, View):
    """
    Vista que marca todas las notificaciones no leídas del usuario como leídas.
    Se ejecuta cuando el usuario hace clic en "Marcar todas como leídas".
    """
    def post(self, request):
        Notificacion.objects.filter(usuario=self.request.user, leido=False).update(leido=True)

        return redirect('viajes:notificaciones')


class EliminarNotificacionView(LoginRequiredMixin, View):
    """
    Vista que elimina una notificación específica del usuario.
    Se usa cuando el usuario quiere borrar una notificación individual.
    Devuelve una respuesta JSON indicando si se eliminó correctamente.
    """
    def post(self, request, *args, **kwargs):
        notificacion_id = self.kwargs.get('pk')
        notificacion = get_object_or_404(Notificacion, pk=notificacion_id)
        notificacion.delete()

        return JsonResponse({'success': True})

def fetch_sugerencias_overpass(ciudad, pais, limite=5):
    """
    Función que busca lugares turísticos en una ciudad usando OpenStreetMap.
    Primero busca las coordenadas de la ciudad, luego busca puntos de interés cercanos.
    Filtra hoteles y hostales para mostrar solo lugares turísticos reales.
    Devuelve una lista de sugerencias con el nombre y tipo de lugar.
    """
    # Geocodificar con Nominatim (es el geocodificador de OpenStreetMap)
    nominatim_url = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&q=' + urllib.parse.quote(f"{ciudad}, {pais}")
    with urllib.request.urlopen(nominatim_url) as resp:
        results = json.loads(resp.read().decode())
    if not results:
        return []
    lat = results[0]['lat']
    lon = results[0]['lon']

    # Query Overpass aprox 10km de radio
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

    # Mezclo y formateo
    random.shuffle(filtrados)
    sugerencias = []
    for el in filtrados[:limite]:
        tags = el.get('tags', {})
        nombre = tags.get('name')
        tipo = tags.get('tourism', tags.get('historic', 'Desconocido'))
        sugerencias.append(f"{nombre} ({tipo})")

    return sugerencias


def fetch_sugerencias_gemini(ciudad, pais, limite=5):
    """
    Función que usa la IA de Google Gemini para generar sugerencias de lugares turísticos.
    Le pide a Gemini que sugiera actividades y lugares interesantes en una ciudad específica.
    Formatea las respuestas para que se vean bonitas con títulos en azul.
    Es una alternativa más inteligente a buscar en mapas.
    """
    api_key = settings.GEMINI_API_KEY or ""

    if not api_key:
        return []

    prompt_text = (
        f"Soy un asistente de viajes. Por favor, dame {limite} sugerencias "
        f"de actividades turísticas o lugares interesantes para visitar en "
        f"{ciudad}, {pais}. "
        f"Incluye el nombre breve de cada lugar/actividad y una descripción muy corta."
        f"Usa lenguaje cercano, en español castallano y no empieces la frase introductoria con ¡Claro!."
    )

    endpoint = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-001:generateContent"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt_text
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 256,
            "topP": 0.95,
            "topK": 40
        }
    }

    params = {"key": api_key}

    try:
        respuesta = requests.post(endpoint, headers=headers, params=params, json=body, timeout=10)
        data = respuesta.json()

        try:
            contenido = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return []

        if not contenido:
            return []

        lineas = [linea.strip() for linea in contenido.split("\n") if linea.strip()]
        sugerencias = []
        for linea in lineas:
            if len(linea) > 2 and linea[0].isdigit() and (linea[1] in [".", ")", "-"]):
                texto = linea[2:].strip()
            elif len(linea) > 3 and linea[:2].isdigit() and (linea[2] in [".", ")", "-"]):
                texto = linea[3:].strip()
            else:
                texto = linea

            if texto.startswith("**") and "**" in texto[2:]:
                texto = texto[2:]
                texto = texto.replace("**", "", 1)

            if ':' in texto:
                titulo, descripcion = texto.split(':', 1)
                texto_formateado = f"<strong style='color:#0d6efd;'>{titulo.strip()}:</strong>{descripcion}"
            else:
                texto_formateado = texto

            if texto:
                sugerencias.append(texto_formateado)

        return sugerencias[:limite]

    except requests.RequestException as e:
        return []

@csrf_exempt
def asistente_ayuda(request):
    """
    Vista que maneja el chat con TravesIA, el asistente virtual de la aplicación.
    Recibe mensajes del usuario y usa Gemini para dar respuestas sobre cómo usar PlanMyTrip.
    Mantiene un historial de la conversación en la sesión del usuario.
    """
    if request.method != 'POST':
        return JsonResponse({'respuesta': 'Método no permitido.'}, status=405)

    datos = json.loads(request.body)
    mensaje = datos.get('mensaje', '').strip()
    if not mensaje:
        return JsonResponse({'respuesta': '¿Podrías escribir una pregunta?'})

    historial = request.session.get('historial_ayuda', [])

    historial.append({'role': 'user', 'text': mensaje})

    respuesta = obtener_respuesta_gemini(historial)

    historial.append({'role': 'model', 'text': respuesta})

    request.session['historial_ayuda'] = historial
    print('Historial de ayuda: {}'.format(historial))
    print('Respuesta de ayuda: {}'.format(respuesta))

    return JsonResponse({'respuesta': respuesta})

def obtener_respuesta_gemini(historial):
    """
    Función que envía el historial de conversación a Gemini y obtiene una respuesta.
    Configura a Gemini como TravesIA, un asistente especializado en PlanMyTrip.
    Le dice que sea simpático, breve y que use emojis en sus respuestas.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "No se ha configurado la API de Gemini."

    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    contents = [{
        "role": h["role"],
        "parts": [{"text": h["text"]}]
    } for h in historial]

    if not any(msg["role"] == "model" for msg in historial):
        system_prompt = {
            "role": "user",
            "parts": [{
                "text": (
                    "Te llamas TravesIA, perteneces a la aplicación PlanMyTrip. Eres un asistente muy simpáticon que ayuda a los usuarios con dudas sobre la aplicación PlanMyTrip.\n"
                    "PlanMyTrip permite crear viajes en grupo, enviar solicitudes de amistad, dar likes a actividades y viajes, crear itinerarios "
                    "y gestionar gastos compartidos de forma equitativa \n"
                    "Cuando te pregunten por destinos o presupuesto, sugiere tres opciones concretas y coherentes según preferencias y presupuesto. "
                    "Responde de manera muy breve, responde un texto de como máximo dos líneas, con emojis, muy agradable, amigable y claro."
                    "Nunca dejes una respuesta incompleta. Si tu máximo es de 100 output tokens, ajusta siempre la respuesta a ese tamaño para que esté completa."
                )
            }]
        }
        contents.insert(0, system_prompt)

    body = {
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 100}
    }

    try:
        resp = requests.post(url, headers=headers, params=params, json=body, timeout=10)
        data = resp.json()
        print("Respuesta cruda de Gemini:", data)
        respuesta =  data['candidates'][0]['content']['parts'][0]['text'].strip()
        return respuesta.replace('*', '')
    except Exception as e:
        print("Error al llamar a Gemini:", e)
        return "Hubo un problema al contactar con el asistente."


PAISES_EUROPEOS = [
    'España', 'Francia', 'Alemania', 'Italia', 'Portugal',
    'Reino Unido', 'Países Bajos', 'Bélgica', 'Grecia',
    'Suecia', 'Noruega', 'Dinamarca', 'Polonia', 'Austria',
    'Suiza', 'Irlanda', 'Finlandia', 'Hungría', 'República Checa',
]

class ViajesPublicosView(LoginRequiredMixin, ListView):
    """
    Vista que muestra todos los viajes públicos que han creado otros usuarios.
    Permite filtrar por destino, continente (Europa u otros), y grupos pequeños.
    También se puede ordenar por fecha del viaje, popularidad (más likes) o alfabéticamente.
    Calcula el presupuesto estimado por persona para cada viaje mostrado.
    """
    model = Viaje
    template_name = 'viajes/viajes_publicos.html'
    context_object_name = 'viajes'
    paginate_by = 12

    def get_queryset(self):
        qs = Viaje.objects.filter(visibilidad='PUBLICO')
        termino = self.request.GET.get('destino', '').strip()

        if termino:
            qs = qs.filter(
                Q(destino__nombre__icontains=termino) |
                Q(destino__pais__icontains=termino)
            )
        else:
            if self.request.GET.get('continente') == 'europa':
                qs = qs.filter(destino__pais__in=PAISES_EUROPEOS)
            elif self.request.GET.get('continente') == 'otros':
                qs = qs.exclude(destino__pais__in=PAISES_EUROPEOS)

        if self.request.GET.get('grupos_reducidos') == '1':
            qs = qs.annotate(num_colaboradores=Count('colaboradores')).filter(num_colaboradores__lte=3)

        orden = self.request.GET.get('orden')

        if orden == 'fecha_viaje':
            qs = qs.order_by('fecha_inicio')
        elif orden == 'populares':
            qs = qs.annotate(num_likes=Count('me_gustas_viaje')).order_by('-num_likes')
        elif orden == 'alfabetico':
            qs = qs.order_by('nombre')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viajes = context['viajes']
        usuario = self.request.user
        context['orden'] = self.request.GET.get('orden', '')

        liked_qs = MeGusta.objects.filter(usuario=usuario, viaje__isnull=False) \
            .values_list('viaje_id', flat=True)
        context['liked_viajes_ids'] = set(liked_qs)

        for viaje in viajes:
            num_participantes = 1 + viaje.colaboradores.count()

            resultado_act = viaje.actividades.aggregate(total_act=Sum('coste_estimado'))
            total_act = resultado_act['total_act'] or Decimal('0.00')

            resultado_gas = Gasto.objects.filter(viaje=viaje).aggregate(total_gas=Sum('cantidad'))
            total_gas = resultado_gas['total_gas'] or Decimal('0.00')

            if num_participantes > 0:
                gasto_por_persona = total_gas / num_participantes
            else:
                gasto_por_persona = Decimal('0.00')

            presupuesto = total_act + gasto_por_persona
            viaje.presupuesto_estimado_por_persona = presupuesto.quantize(Decimal('0.01'))

        context['filtro_destino'] = self.request.GET.get('destino', '').strip()
        context['filtro_continente'] = self.request.GET.get('continente', '')
        context['filtro_grupos_reducidos'] = self.request.GET.get('grupos_reducidos', '')

        return context

class ToggleLikeViajeView(LoginRequiredMixin, View):
    """
    Vista que maneja cuando un usuario le da "me gusta" a un viaje.
    Funciona igual que los likes de actividades: si ya tenía like se lo quita, si no lo tenía se lo pone.
    Envía una notificación al creador del viaje cuando alguien le da like.
    """
    def post(self, request, pk):
        viaje = get_object_or_404(Viaje, pk=pk)
        usuario = request.user

        like_obj, created = MeGusta.objects.get_or_create(usuario=usuario, viaje=viaje, defaults={'actividad': None})

        if created:
            if viaje.creador != usuario:
                mensaje = f"A {usuario.username} le gustó tu viaje: {viaje.nombre}"
                enlace = reverse('viajes:detalles_viaje', kwargs={'pk': viaje.pk})
                Notificacion.objects.create(usuario=viaje.creador, mensaje=mensaje, tipo='OTROS', enlace_relacionado=enlace)
            liked = True
        else:
            like_obj.delete()
            liked = False

        total = viaje.me_gustas_viaje.count()
        return JsonResponse({'liked': liked, 'count': total})

class ViajeLikesView(LoginRequiredMixin, View):
    """
    Vista que devuelve la lista de usuarios que le han dado like a un viaje.
    Se usa para mostrar quién le gustó el viaje cuando haces clic en el contador de likes.
    Devuelve el nombre de usuario y la foto de perfil de cada persona.
    """
    def get(self, request, pk):
        viaje = get_object_or_404(Viaje, pk=pk)
        usuarios = viaje.me_gustas_viaje.select_related('usuario').all()
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

class GastosPorCategoriaAPI(APIView):
    """
    API que devuelve el total de gastos agrupados por categoría para un viaje específico.
    Se usa para generar gráficas que muestren en qué se gasta más dinero durante el viaje.
    Por ejemplo: cuánto se gastó en comida, transporte, alojamiento, etc.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, viaje_id):
        viaje = get_object_or_404(Viaje, pk=viaje_id)
        gastos = (Gasto.objects.filter(viaje=viaje).values('categoria').annotate(total=Sum('cantidad')).order_by('categoria'))
        data = {
            "viaje_id": viaje.id,
            "totales_por_categoria": [
                { "categoria": g['categoria'], "total": float(g['total']) }
                for g in gastos
            ]
        }
        return Response(data)