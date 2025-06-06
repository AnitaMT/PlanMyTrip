from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.urls import path

import views
from viajes.views import *

app_name = 'viajes'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', UsuarioLogoutView.as_view(), name='logout'),
    path('inicio/', PaginaInicioUsuarioView.as_view(), name='inicio'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('crear-viaje/', CrearViajeView.as_view(), name='crear_viaje'),
    path('<int:pk>/', DetallesViajeView.as_view(), name='detalles_viaje'),
    path('<int:pk>/editar-viaje/', EditarViajeView.as_view(), name='editar_viaje'),
    path('<int:pk>/eliminar-viaje/', EliminarViajeView.as_view(), name='eliminar_viaje'),
    path('amistad/enviar/<int:pk>/', EnviarSolicitudView.as_view(), name='enviar_solicitud'),
    path('amistad/usuarios/', UsuariosDisponiblesView.as_view(), name='usuarios_disponibles'),
    path('amistad/recibidas/', ListaSolicitudesView.as_view(), name='solicitudes_recibidas'),
    path('amistad/responder/<int:pk>/', ResponderSolicitudView.as_view(), name='responder_solicitud'),
    path('eliminar_amigo/<int:pk>/', EliminarAmigoView.as_view(), name='eliminar_amigo'),
    path('amistad/lista/', ListaAmigosView.as_view(), name='lista_amigos'),
    path('<int:viaje_id>/agregar-colaborador/', AgregarColaboradorView.as_view(), name='agregar_colaborador'),
    path('viaje/<int:viaje_id>/colaborador/<int:pk>/eliminar-colaborador/', EliminarColaboradorView.as_view(), name='eliminar_colaborador'),
    path('actividad/<int:pk>/detalles-actividad/', DetallesActividadView.as_view(), name='detalles_actividad'),
    path('<int:pk>/agregar-actividad/', AgregarActividadView.as_view(), name='agregar_actividad'),
    path('actividad/<int:pk>/editar/', EditarActividadView.as_view(), name='editar_actividad'),
    path('actividad/<int:pk>/eliminar/', EliminarActividadView.as_view(), name='eliminar-actividad'),
    path('<int:pk>/gastos/', ListaGastosView.as_view(), name='lista_gastos'),
    path('<int:pk>/agregar-gasto/', AgregarGastoView.as_view(), name='agregar_gasto'),
    path('eliminar_gasto/<int:pk>/', EliminarGastoView.as_view(), name='eliminar_gasto'),
    path('<int:viaje_id>/deudas/', calcular_deudas, name='calcular_deudas'),
    path('actividad/<int:pk>/toggle-like/', LikeToggleView.as_view(), name='toggle_like'),
    path('actividad/<int:pk>/likes/', ActividadLikesView.as_view(),name='actividad_likes'),
    path('ajustes-usuario/', AjustesUsuarioView.as_view(),name='ajustes_usuario'),
    path('notificaciones/<int:pk>/', NotificacionRedirectView.as_view(), name='notificacion_redireccion'),
    path('notificaciones/', NotificacionListView.as_view(), name='notificaciones'),
    path('notificaciones/marcar-todas/', MarcarTodasLeidasView.as_view(), name='notificaciones_marcar_todas'),
    path('notificaciones/<int:pk>/eliminar-notificacion/', EliminarNotificacionView.as_view(), name='eliminar_notificacion'),
    path('viajes_publicos/', ViajesPublicosView.as_view(), name='viajes_publicos'),
    path('toggle-like-viaje/<int:pk>/', ToggleLikeViajeView.as_view(), name='toggle_like_viaje'),
    path('likes/viaje/<int:pk>/', ViajeLikesView.as_view(), name='likes_viaje'),
    path('asistente/', views.asistente_ayuda, name='asistente_ayuda'),
]
