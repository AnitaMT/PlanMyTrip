from django.db import migrations


def agregar_colaboradores(apps, schema_editor):
    Viaje = apps.get_model('viajes', 'Viaje')
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')

    creadores_por_viaje = {
        'Japón con Jamón': 'emilio',
        'Aventuras por Edimburgo': 'belen',
        'Ruta Espagueti': 'vicenta',
        'Hawaii que Guay': 'juan',
        'Viva Las Vegas': 'paloma',
        'Paella por Marbella': 'emilio',
        'Disneyland París': 'mariano',
        'No me mola ir a Londres sola': 'isabel',
        'Grecia con Gracia': 'marisa',
        'Exploradores por Egipto': 'marisa'
    }

    colaboradores_por_viaje = {
        'Japón con Jamón': ['vicenta', 'belen', 'juan', 'isabel'],
        'Aventuras por Edimburgo': ['emilio', 'isabel', 'mariano'],
        'Ruta Espagueti': ['mariano', 'marisa', 'paloma', 'juan'],
        'Hawaii que Guay': ['belen', 'vicenta', 'isabel', 'marisa', 'paloma'],
        'Viva Las Vegas': ['juan', 'emilio', 'concha', 'mauri', 'belen'],
        'Paella por Marbella': ['vicenta', 'belen', 'juan', 'isabel', 'mariano'],
        'Disneyland París': ['paloma', 'concha'],
        'No me mola ir a Londres sola': ['belen', 'vicenta', 'marisa'],
        'Grecia con Gracia': ['emilio', 'juan', 'isabel', 'paloma'],
        'Exploradores por Egipto': ['vicenta', 'belen', 'mariano', 'paloma', 'mauri', 'isabel', 'juan']
    }

    for viaje in Viaje.objects.all():
        nombre_viaje = viaje.nombre
        creador_username = creadores_por_viaje.get(nombre_viaje)

        if nombre_viaje in colaboradores_por_viaje:
            usernames = [u for u in colaboradores_por_viaje[nombre_viaje]
                         if u != creador_username]

            colaboradores = UsuarioPersonalizado.objects.filter(username__in=usernames)
            viaje.colaboradores.add(*colaboradores)
            viaje.save()


def quitar_colaboradores(apps, schema_editor):
    Viaje = apps.get_model('viajes', 'Viaje')
    for viaje in Viaje.objects.all():
        viaje.colaboradores.clear()


class Migration(migrations.Migration):
    dependencies = [
        ('viajes', '0009_poblacion_db'),
    ]

    operations = [
        migrations.RunPython(agregar_colaboradores, quitar_colaboradores),
    ]