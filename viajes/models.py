from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator



class UsuarioPersonalizado(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    foto_perfil = models.ImageField(upload_to="fotos_perfil/", null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    groups = models.ManyToManyField('auth.Group', related_name="usuarios_personalizados", blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name="usuarios_personalizados", blank=True)
    amigos = models.ManyToManyField('self', symmetrical=True, related_name="amigos_de", blank=True)

    def __str__(self):
        return self.username



class Destino(models.Model):
    CATEGORIAS_DESTINO = [
        ('PLAYA', 'Playa'),
        ('CIUDAD', 'Ciudad'),
        ('MONTAÑA', 'Montaña'),
        ('RURAL', 'Rural'),
        ('CULTURAL', 'Cultural')
    ]

    nombre = models.CharField(max_length=255)
    pais = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to="destinos/", null=True, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_DESTINO, default='CIUDAD', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre}, {self.pais}"



class Viaje(models.Model):
    ESTADOS_VIAJE = [
        # ('PLANIFICACION', 'En Planificación'),
        ('ACTIVO', 'Activo'),
        ('FINALIZADO', 'Finalizado')
    ]

    VISIBILIDAD_VIAJE = [
        ('PRIVADO', 'Privado'),
        ('PUBLICO', 'Público')
    ]

    nombre = models.CharField(max_length=255)
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name="viajes")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    creador = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="viajes_creados")
    colaboradores = models.ManyToManyField(UsuarioPersonalizado, related_name="viajes_colaborando", blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_VIAJE, default='ACTIVO')
    presupuesto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    visibilidad = models.CharField(max_length=20, choices=VISIBILIDAD_VIAJE, default='PRIVADO')
    imagen = models.ImageField(upload_to="viaje/", null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.destino.nombre}"



class Actividad(models.Model):
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta')
    ]

    CATEGORIAS = [
        ('GASTRONOMIA', 'Gastronomía'),
        ('CULTURAL', 'Cultural'),
        ('AVENTURA', 'Aventura'),
        ('RELAX', 'Relax'),
        ('OTROS', 'Otros')
    ]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="actividades")
    creador = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="actividades_creadas")
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fecha_hora = models.DateTimeField()
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='MEDIA')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='OTROS')
    coste_estimado = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)

    def __str__(self):
        return f"{self.titulo} en {self.viaje.nombre}"



class Comentario(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="comentarios_realizados")
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.actividad.titulo}"



class MeGusta(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name="me_gustas", null=True, blank=True)
    usuario = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="me_gustas_dados")
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="me_gustas_viaje", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'actividad'],
                name='unique_like_actividad',
                condition=models.Q(actividad__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['usuario', 'viaje'],
                name='unique_like_viaje',
                condition=models.Q(viaje__isnull=False)
            ),
        ]

    def __str__(self):
        if self.actividad:
            return f"{self.usuario.username} le dio me gusta a la actividad: {self.actividad.titulo}"
        if self.viaje:
            return f"{self.usuario.username} le dio me gusta al viaje: {self.viaje.nombre}"
        return f"{self.usuario.username} hizo un MeGusta inválido"



class Gasto(models.Model):
    CATEGORIAS_GASTO = [
        ('ALOJAMIENTO', 'Alojamiento'),
        ('COMIDA', 'Comida'),
        ('TRANSPORTE', 'Transporte'),
        ('ACTIVIDADES', 'Actividades'),
        ('OTROS', 'Otros')
    ]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="gastos")
    pagador = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="gastos_pagados")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    fecha = models.DateField(auto_now_add=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_GASTO, default='OTROS')
    comprobante = models.ImageField(upload_to="comprobantes/", null=True, blank=True)

    def __str__(self):
        return f"{self.pagador.username} pagó {self.cantidad}€ en {self.descripcion}"



class DivisionGasto(models.Model):
    gasto = models.ForeignKey(Gasto, on_delete=models.CASCADE, related_name="divisiones")
    deudor = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="deudas")
    cantidad_a_pagar = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField(null=True, blank=True)
    pagado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.deudor.username} debe {self.cantidad_a_pagar}€ en {self.gasto.descripcion} a {self.gasto.pagador.username}"



class Notificacion(models.Model):
    TIPOS_NOTIFICACION = [
        ('GASTO', 'Nuevo Gasto'),
        ('ACTIVIDAD', 'Nueva Actividad'),
        ('COMENTARIO', 'Nuevo Comentario'),
        ('COLABORADOR', 'Nuevo Colaborador'),
        ('PAGO', 'Recordatorio de Pago'),
        ('SOLICITUD_AMISTAD', 'Solicitud de Amistad'),
        ('SOLICITUD_ACEPTADA', 'Solicitud Aceptada'),
        ('OTROS', 'Otros')
    ]

    usuario = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name="notificaciones")
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    tipo = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION, default='OTROS')
    enlace_relacionado = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje}"


class SugerenciaIA(models.Model):
    TIPOS_SUGERENCIA = [
        ('ACTIVIDAD', 'Actividad'),
        ('LUGAR', 'Lugar de Interés'),
        ('RESTAURANTE', 'Restaurante'),
        ('RUTA', 'Ruta Turística')
    ]

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE)
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE)
    usuario = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS_SUGERENCIA)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sugerencia de {self.tipo} para {self.destino.nombre}"

class SolicitudAmistad(models.Model):
    emisor = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    receptor = models.ForeignKey(UsuarioPersonalizado, on_delete=models.CASCADE, related_name='solicitudes_recibidas')
    fecha = models.DateTimeField(auto_now_add=True)
    aceptada = models.BooleanField(null=True)

    class Meta:
        unique_together = ('emisor', 'receptor')

    def __str__(self):
        estado = 'pendiente' if self.aceptada is None else ('aceptada' if self.aceptada else 'rechazada')
        return f"{self.emisor}→{self.receptor} ({estado})"
