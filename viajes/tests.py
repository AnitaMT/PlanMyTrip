from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from viajes.views import *
from viajes.forms import RegistroUsuarioForm, CrearViajeForm, AgregarActividadForm
import json
from decimal import Decimal
import datetime

User = get_user_model()


class IndexViewTest(TestCase):
    def test_index_view(self):
        response = self.client.get(reverse('viajes:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/index.html')


class RegistroUsuarioViewTest(TestCase):
    def test_registro_view_get(self):
        response = self.client.get(reverse('viajes:registro'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/registro.html')
        self.assertIsInstance(response.context['form'], RegistroUsuarioForm)

    def test_registro_view_post_success(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(reverse('viajes:registro'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('viajes:login'))

        # Verificar que el usuario fue creado
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Verificar el mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '¡Registro exitoso! Ahora puedes iniciar sesión.')


class UsuarioLoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('viajes:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_view_post_success(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('viajes:login'), data, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_view_post_invalid(self):
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(reverse('viajes:login'), data)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertIn('error', response.context)


class PaginaInicioUsuarioViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Crear datos de prueba
        self.destino = Destino.objects.create(
            nombre='Paris',
            pais='Francia'
        )
        self.viaje_activo = Viaje.objects.create(
            nombre='Viaje a Paris',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=7),
            creador=self.user,
            estado='ACTIVO'
        )
        self.viaje_finalizado = Viaje.objects.create(
            nombre='Viaje a Londres',
            destino=Destino.objects.create(nombre='Londres', pais='Reino Unido'),
            fecha_inicio=datetime.date.today() - datetime.timedelta(days=30),
            fecha_fin=datetime.date.today() - datetime.timedelta(days=23),
            creador=self.user,
            estado='FINALIZADO'
        )
        self.notificacion = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Test notification',
            leido=False
        )

    def test_pagina_inicio_view(self):
        response = self.client.get(reverse('viajes:inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/pagina_inicio.html')

        # Verificar que los viajes aparecen en el contexto
        self.assertIn('viajes_activos', response.context)
        self.assertIn('viajes_finalizados', response.context)

        # Verificar las notificaciones
        self.assertEqual(response.context['notificaciones_sin_leer_count'], 1)
        self.assertEqual(len(response.context['ultimas_notificaciones']), 1)


class CrearViajeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_crear_viaje_view_get(self):
        response = self.client.get(reverse('viajes:crear_viaje'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/crear_viaje.html')
        self.assertIsInstance(response.context['form'], CrearViajeForm)

    def test_crear_viaje_view_post_success(self):
        data = {
            'nombre': 'Nuevo Viaje',
            'destino_nombre': 'Barcelona, España',
            'categoria_destino': 'CIUDAD',
            'fecha_inicio': '2023-12-01',
            'fecha_fin': '2023-12-10',
            'visibilidad': 'PUBLICO'
        }
        response = self.client.post(reverse('viajes:crear_viaje'), data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('viajes:inicio'))

        # Verificar que el viaje fue creado
        self.assertTrue(Viaje.objects.filter(nombre='Nuevo Viaje').exists())

        # Verificar que el destino fue creado
        destino = Destino.objects.get(nombre='Barcelona')
        self.assertEqual(destino.pais, 'España')


class DetallesViajeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.destino = Destino.objects.create(
            nombre='Roma',
            pais='Italia'
        )
        self.viaje = Viaje.objects.create(
            nombre='Viaje a Roma',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=7),
            creador=self.user
        )

        # Crear gastos y divisiones para probar las deudas
        self.gasto = Gasto.objects.create(
            viaje=self.viaje,
            pagador=self.user,
            cantidad=Decimal('100.00'),
            descripcion='Hotel'
        )
        self.colaborador = User.objects.create_user(
            username='colab',
            email='colab@example.com',
            password='testpass123'
        )
        self.viaje.colaboradores.add(self.colaborador)

        DivisionGasto.objects.create(
            gasto=self.gasto,
            deudor=self.colaborador,
            cantidad_a_pagar=Decimal('50.00')
        )

    def test_detalles_viaje_view(self):
        response = self.client.get(reverse('viajes:detalles_viaje', kwargs={'pk': self.viaje.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/detalles_viaje.html')

        # Verificar que el viaje está en el contexto
        self.assertEqual(response.context['viaje'], self.viaje)

        # Verificar las deudas
        self.assertIn('deudas', response.context)
        self.assertIn('colab', response.context['deudas'])
        self.assertEqual(response.context['deudas']['colab'], Decimal('50.00'))


class AgregarColaboradorViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.amigo = User.objects.create_user(
            username='amigo',
            email='amigo@example.com',
            password='testpass123'
        )
        self.user.amigos.add(self.amigo)

        self.destino = Destino.objects.create(
            nombre='Madrid',
            pais='España'
        )
        self.viaje = Viaje.objects.create(
            nombre='Viaje a Madrid',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=5),
            creador=self.user
        )

    def test_agregar_colaborador(self):
        data = json.dumps({'usuario_id': self.amigo.id})
        request = self.factory.post(
            reverse('viajes:agregar_colaborador', kwargs={'viaje_id': self.viaje.id}),
            data=data,
            content_type='application/json'
        )
        request.user = self.user

        response = AgregarColaboradorView.as_view()(request, viaje_id=self.viaje.id)
        response_data = json.loads(response.content)

        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['username'], 'amigo')

        # Verificar que el amigo fue agregado como colaborador
        self.assertTrue(self.viaje.colaboradores.filter(id=self.amigo.id).exists())

        # Verificar que se creó una notificación
        self.assertTrue(Notificacion.objects.filter(usuario=self.amigo).exists())


class AgregarActividadViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.destino = Destino.objects.create(
            nombre='Berlin',
            pais='Alemania'
        )
        self.viaje = Viaje.objects.create(
            nombre='Viaje a Berlin',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=7),
            creador=self.user
        )

    def test_agregar_actividad_view_get(self):
        response = self.client.get(reverse('viajes:agregar_actividad', kwargs={'pk': self.viaje.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/agregar_actividad.html')
        self.assertIsInstance(response.context['form'], AgregarActividadForm)

    def test_agregar_actividad_view_post_success(self):
        data = {
            'titulo': 'Visita al Muro',
            'descripcion': 'Visita guiada al Muro de Berlin',
            'fecha_hora': '2023-12-01 10:00',
            'prioridad': 'ALTA',
            'categoria': 'CULTURAL',
            'coste_estimado': '20.00'
        }
        response = self.client.post(
            reverse('viajes:agregar_actividad', kwargs={'pk': self.viaje.pk}),
            data
        )

        self.assertEqual(response.status_code, 302)

        # Verificar que la actividad fue creada
        self.assertTrue(Actividad.objects.filter(titulo='Visita al Muro').exists())


class AgregarGastoViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.destino = Destino.objects.create(
            nombre='Lisboa',
            pais='Portugal'
        )
        self.viaje = Viaje.objects.create(
            nombre='Viaje a Lisboa',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=5),
            creador=self.user
        )
        self.colaborador = User.objects.create_user(
            username='colab',
            email='colab@example.com',
            password='testpass123'
        )
        self.viaje.colaboradores.add(self.colaborador)

    def test_agregar_gasto_view_get(self):
        response = self.client.get(reverse('viajes:agregar_gasto', kwargs={'pk': self.viaje.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'viajes/agregar_gasto.html')

    def test_agregar_gasto_view_post_success(self):
        data = {
            'cantidad': '100.00',
            'descripcion': 'Hotel',
            'categoria': 'ALOJAMIENTO',
            'participantes': [self.user.id, self.colaborador.id]
        }
        response = self.client.post(
            reverse('viajes:agregar_gasto', kwargs={'pk': self.viaje.pk}),
            data
        )

        self.assertEqual(response.status_code, 302)

        # Verificar que el gasto fue creado
        self.assertTrue(Gasto.objects.filter(descripcion='Hotel').exists())

        # Verificar que se crearon las divisiones de gasto
        gasto = Gasto.objects.get(descripcion='Hotel')
        self.assertEqual(gasto.divisiones.count(), 2)


class LikeToggleViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.destino = Destino.objects.create(
            nombre='Viena',
            pais='Austria'
        )
        self.viaje = Viaje.objects.create(
            nombre='Viaje a Viena',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=5),
            creador=self.user
        )
        self.actividad = Actividad.objects.create(
            viaje=self.viaje,
            creador=self.user,
            titulo='Visita al Palacio',
            fecha_hora=datetime.datetime.now() + datetime.timedelta(days=1)
        )

    def test_toggle_like(self):
        # Primer like
        response = self.client.post(
            reverse('viajes:toggle_like', kwargs={'pk': self.actividad.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['liked'])
        self.assertEqual(response_data['count'], 1)

        # Verificar que se creó el like
        self.assertTrue(MeGusta.objects.filter(actividad=self.actividad, usuario=self.user).exists())

        # Segundo like (debe eliminarlo)
        response = self.client.post(
            reverse('viajes:toggle_like', kwargs={'pk': self.actividad.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['liked'])
        self.assertEqual(response_data['count'], 0)

        # Verificar que se eliminó el like
        self.assertFalse(MeGusta.objects.filter(actividad=self.actividad, usuario=self.user).exists())


class ToggleLikeViajeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.destino = Destino.objects.create(
            nombre='Praga',
            pais='República Checa'
        )
        self.viaje = Viaje.objects.create(
            nombre='Viaje a Praga',
            destino=self.destino,
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=5),
            creador=self.user,
            visibilidad='PUBLICO'
        )

    def test_toggle_like_viaje(self):
        # Primer like
        response = self.client.post(
            reverse('viajes:toggle_like_viaje', kwargs={'pk': self.viaje.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['liked'])
        self.assertEqual(response_data['count'], 1)

        # Verificar que se creó el like
        self.assertTrue(MeGusta.objects.filter(viaje=self.viaje, usuario=self.user).exists())

        # Segundo like (debe eliminarlo)
        response = self.client.post(
            reverse('viajes:toggle_like_viaje', kwargs={'pk': self.viaje.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['liked'])
        self.assertEqual(response_data['count'], 0)

        self.assertFalse(MeGusta.objects.filter(viaje=self.viaje, usuario=self.user).exists())

