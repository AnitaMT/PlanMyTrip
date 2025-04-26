from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.urls import path
from viajes.views import IndexView, RegistroUsuarioView, UsuarioLoginView, UsuarioLogoutView, PaginaInicioUsuarioView, \
    CrearViajeView, DetallesViajeView, AgregarColaboradorView, EditarActividadView, EliminarActividadView, \
    AgregarActividadView, ListaGastosView, AgregarGastoView, calcular_deudas
from views import EliminarColaboradorView, DetallesActividadView

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
    path('<int:viaje_id>/agregar-colaborador/', AgregarColaboradorView.as_view(), name='agregar_colaborador'),
    path('viaje/<int:viaje_id>/colaborador/<int:pk>/eliminar-colaborador/', EliminarColaboradorView.as_view(), name='eliminar_colaborador'),
    path('actividad/<int:pk>/detalles-actividad/', DetallesActividadView.as_view(), name='detalles_actividad'),
    path('<int:pk>/agregar-actividad/', AgregarActividadView.as_view(), name='agregar_actividad'),
    path('actividad/<int:pk>/editar/', EditarActividadView.as_view(), name='editar_actividad'),
    path('actividad/<int:pk>/eliminar/', EliminarActividadView.as_view(), name='eliminar-actividad'),
    path('<int:pk>/gastos/', ListaGastosView.as_view(), name='lista_gastos'),
    path('<int:pk>/agregar-gasto/', AgregarGastoView.as_view(), name='agregar_gasto'),
    path('<int:viaje_id>/deudas/', calcular_deudas, name='calcular_deudas'),

]