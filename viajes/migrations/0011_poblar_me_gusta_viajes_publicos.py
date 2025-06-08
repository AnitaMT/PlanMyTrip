from django.db import migrations
import random


def poblar_megustas_viajes(apps, schema_editor):
    MeGusta = apps.get_model('viajes', 'MeGusta')
    Viaje = apps.get_model('viajes', 'Viaje')
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')

    viajes_publicos = Viaje.objects.filter(visibilidad='PUBLICO')

    usuarios = UsuarioPersonalizado.objects.all()

    for viaje in viajes_publicos:
        num_likes = random.randint(1, len(usuarios))

        usuarios_posibles = [u for u in usuarios]
        usuarios_like = random.sample(list(usuarios_posibles), min(num_likes, len(usuarios_posibles)))

        for usuario in usuarios_like:
            MeGusta.objects.create(
                viaje=viaje,
                usuario=usuario
            )


def eliminar_megustas_viajes(apps, schema_editor):
    MeGusta = apps.get_model('viajes', 'MeGusta')
    MeGusta.objects.filter(viaje__isnull=False).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('viajes', '0010_agregar_colaboradores_viaje'),
    ]

    operations = [
        migrations.RunPython(poblar_megustas_viajes, eliminar_megustas_viajes),
    ]