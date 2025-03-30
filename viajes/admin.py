from django.contrib import admin

from viajes.models import UsuarioPersonalizado, Destino, Viaje, Actividad, Comentario, MeGusta, Gasto, DivisionGasto, \
    Notificacion, SugerenciaIA

admin.site.register(UsuarioPersonalizado)
admin.site.register(Destino)
admin.site.register(Viaje)
admin.site.register(Actividad)
admin.site.register(Comentario)
admin.site.register(MeGusta)
admin.site.register(Gasto)
admin.site.register(DivisionGasto)
admin.site.register(Notificacion)
admin.site.register(SugerenciaIA)

