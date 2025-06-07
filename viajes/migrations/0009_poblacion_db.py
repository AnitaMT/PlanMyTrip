from django.db import migrations
from datetime import datetime


def poblar_destinos(apps, schema_editor):
    Destino = apps.get_model('viajes', 'Destino')

    destinos = [
        {'nombre': 'Tokio', 'pais': 'Japón', 'categoria': 'CIUDAD', 'descripcion': 'La vibrante capital de Japón'},
        {'nombre': 'Edimburgo', 'pais': 'Escocia', 'categoria': 'CIUDAD', 'descripcion': 'Ciudad histórica escocesa'},
        {'nombre': 'Roma', 'pais': 'Italia', 'categoria': 'CULTURAL', 'descripcion': 'La ciudad eterna'},
        {'nombre': 'Honolulu', 'pais': 'Hawaii', 'categoria': 'PLAYA', 'descripcion': 'Paraíso tropical'},
        {'nombre': 'Las Vegas', 'pais': 'Estados Unidos', 'categoria': 'CIUDAD',
         'descripcion': 'La ciudad del entretenimiento'},
        {'nombre': 'Marbella', 'pais': 'España', 'categoria': 'PLAYA', 'descripcion': 'Costa del Sol española'},
        {'nombre': 'París', 'pais': 'Francia', 'categoria': 'CULTURAL', 'descripcion': 'La ciudad de la luz'},
        {'nombre': 'Londres', 'pais': 'Reino Unido', 'categoria': 'CIUDAD', 'descripcion': 'Capital británica'},
        {'nombre': 'Santorini', 'pais': 'Grecia', 'categoria': 'PLAYA', 'descripcion': 'Isla griega paradisíaca'},
        {'nombre': 'El Cairo', 'pais': 'Egipto', 'categoria': 'CULTURAL', 'descripcion': 'Cuna de los faraones'},
    ]

    for destino_data in destinos:
        Destino.objects.create(**destino_data)


def poblar_usuarios(apps, schema_editor):
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')

    usuarios = [
        {'username': 'emilio', 'email': 'emilio@mail.com', 'foto_perfil': 'fotos_perfil/emilio.jpeg'},
        {'username': 'vicenta', 'email': 'vicenta@mail.com', 'foto_perfil': 'fotos_perfil/vicenta.webp'},
        {'username': 'belen', 'email': 'belen@mail.com', 'foto_perfil': 'fotos_perfil/belen.webp'},
        {'username': 'juan', 'email': 'juan@mail.com', 'foto_perfil': 'fotos_perfil/juan.webp'},
        {'username': 'isabel', 'email': 'isabel@mail.com', 'foto_perfil': 'fotos_perfil/isabel.webp'},
        {'username': 'mariano', 'email': 'mariano@mail.com', 'foto_perfil': 'fotos_perfil/mariano.jpeg'},
        {'username': 'concha', 'email': 'concha@mail.com', 'foto_perfil': 'fotos_perfil/concha.webp'},
        {'username': 'marisa', 'email': 'marisa@mail.com', 'foto_perfil': 'fotos_perfil/marisa.jpg'},
        {'username': 'mauri', 'email': 'mauri@mail.com', 'foto_perfil': 'fotos_perfil/mauri.webp'},
        {'username': 'paloma', 'email': 'paloma@mail.com', 'foto_perfil': 'fotos_perfil/paloma.webp'},
    ]

    for usuario_data in usuarios:
        UsuarioPersonalizado.objects.create(**usuario_data)


def poblar_viajes(apps, schema_editor):
    Viaje = apps.get_model('viajes', 'Viaje')
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')
    Destino = apps.get_model('viajes', 'Destino')

    viajes_data = [
        {'nombre': 'Japón con Jamón', 'destino_nombre': 'Tokio', 'fecha_inicio': '2025-06-07',
         'fecha_fin': '2025-07-07', 'creador_username': 'emilio', 'imagen': 'viaje/tokio.jpg'},
        {'nombre': 'Aventuras por Edimburgo', 'destino_nombre': 'Edimburgo', 'fecha_inicio': '2025-08-08',
         'fecha_fin': '2025-08-20', 'creador_username': 'belen', 'imagen': 'viaje/edimburgo.jpg'},
        {'nombre': 'Ruta Espagueti', 'destino_nombre': 'Roma', 'fecha_inicio': '2025-09-09', 'fecha_fin': '2025-09-28',
         'creador_username': 'vicenta', 'imagen': 'viaje/roma.jpg'},
        {'nombre': 'Hawaii que Guay', 'destino_nombre': 'Honolulu', 'fecha_inicio': '2025-06-10',
         'fecha_fin': '2025-07-30', 'creador_username': 'juan', 'imagen': 'viaje/lilo.jpg'},
        {'nombre': 'Viva Las Vegas', 'destino_nombre': 'Las Vegas', 'fecha_inicio': '2025-07-10',
         'fecha_fin': '2025-07-24', 'creador_username': 'paloma', 'imagen': 'viaje/lasvegas.webp'},
        {'nombre': 'Paella por Marbella', 'destino_nombre': 'Marbella', 'fecha_inicio': '2025-08-10',
         'fecha_fin': '2025-08-14', 'creador_username': 'emilio', 'imagen': 'viaje/marbella.jpg'},
        {'nombre': 'Disneyland París', 'destino_nombre': 'París', 'fecha_inicio': '2025-06-07',
         'fecha_fin': '2025-07-07', 'creador_username': 'mariano', 'imagen': 'viaje/disney.jpg'},
        {'nombre': 'No me mola ir a Londres sola', 'destino_nombre': 'Londres', 'fecha_inicio': '2025-11-20',
         'fecha_fin': '2025-11-30', 'creador_username': 'isabel', 'imagen': 'viaje/londres.png'},
        {'nombre': 'Grecia con Gracia', 'destino_nombre': 'Santorini', 'fecha_inicio': '2025-08-12',
         'fecha_fin': '2025-08-20', 'creador_username': 'marisa', 'imagen': 'viaje/santorini.webp'},
        {'nombre': 'Exploradores por Egipto', 'destino_nombre': 'El Cairo', 'fecha_inicio': '2025-10-10',
         'fecha_fin': '2025-10-15', 'creador_username': 'marisa', 'imagen': 'viaje/elcairo.webp'},
    ]

    for viaje_data in viajes_data:
        destino = Destino.objects.get(nombre=viaje_data['destino_nombre'])
        creador = UsuarioPersonalizado.objects.get(username=viaje_data['creador_username'])

        Viaje.objects.create(
            nombre=viaje_data['nombre'],
            destino=destino,
            fecha_inicio=viaje_data['fecha_inicio'],
            fecha_fin=viaje_data['fecha_fin'],
            creador=creador,
            visibilidad='PUBLICO',
            imagen=viaje_data['imagen']
        )


def poblar_actividades(apps, schema_editor):
    Actividad = apps.get_model('viajes', 'Actividad')
    Viaje = apps.get_model('viajes', 'Viaje')
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')

    actividades_data = [
        # Japón con Jamón
        {'viaje_nombre': 'Japón con Jamón', 'creador_username': 'emilio', 'titulo': 'Visita al Templo Senso-ji',
         'descripcion': 'Explorar el templo más antiguo de Tokio', 'fecha_hora': '2025-06-08 10:00:00',
         'ubicacion': 'Asakusa, Tokio', 'prioridad': 'ALTA', 'categoria': 'CULTURAL', 'coste_estimado': 0},
        {'viaje_nombre': 'Japón con Jamón', 'creador_username': 'emilio', 'titulo': 'Sushi en Tsukiji',
         'descripcion': 'Desayuno de sushi fresco en el mercado', 'fecha_hora': '2025-06-09 07:00:00',
         'ubicacion': 'Mercado Tsukiji', 'prioridad': 'ALTA', 'categoria': 'GASTRONOMIA', 'coste_estimado': 45},
        {'viaje_nombre': 'Japón con Jamón', 'creador_username': 'emilio', 'titulo': 'Karaoke en Shibuya',
         'descripcion': 'Noche loca de karaoke japonés', 'fecha_hora': '2025-06-10 22:00:00', 'ubicacion': 'Shibuya',
         'prioridad': 'MEDIA', 'categoria': 'OTROS', 'coste_estimado': 30},

        # Aventuras por Edimburgo
        {'viaje_nombre': 'Aventuras por Edimburgo', 'creador_username': 'belen', 'titulo': 'Castillo de Edimburgo',
         'descripcion': 'Visita al castillo histórico', 'fecha_hora': '2025-08-09 14:00:00', 'ubicacion': 'Castle Rock',
         'prioridad': 'ALTA', 'categoria': 'CULTURAL', 'coste_estimado': 19.50},
        {'viaje_nombre': 'Aventuras por Edimburgo', 'creador_username': 'belen', 'titulo': 'Pub crawl por Royal Mile',
         'descripcion': 'Tour de pubs tradicionales escoceses', 'fecha_hora': '2025-08-10 20:00:00',
         'ubicacion': 'Royal Mile', 'prioridad': 'MEDIA', 'categoria': 'OTROS', 'coste_estimado': 35},
        {'viaje_nombre': 'Aventuras por Edimburgo', 'creador_username': 'belen', 'titulo': 'Hiking por Arthur\'s Seat',
         'descripcion': 'Subida al volcán extinto con vistas de la ciudad', 'fecha_hora': '2025-08-11 08:00:00',
         'ubicacion': 'Holyrood Park', 'prioridad': 'ALTA', 'categoria': 'AVENTURA', 'coste_estimado': 0},

        # Ruta Espagueti
        {'viaje_nombre': 'Ruta Espagueti', 'creador_username': 'vicenta', 'titulo': 'Coliseo Romano',
         'descripcion': 'Visita al anfiteatro más famoso del mundo', 'fecha_hora': '2025-09-10 09:00:00',
         'ubicacion': 'Piazza del Colosseo', 'prioridad': 'ALTA', 'categoria': 'CULTURAL', 'coste_estimado': 16},
        {'viaje_nombre': 'Ruta Espagueti', 'creador_username': 'vicenta', 'titulo': 'Cena en Trastevere',
         'descripcion': 'Pasta auténtica en el barrio bohemio', 'fecha_hora': '2025-09-11 21:00:00',
         'ubicacion': 'Trastevere', 'prioridad': 'ALTA', 'categoria': 'GASTRONOMIA', 'coste_estimado': 28},
        {'viaje_nombre': 'Ruta Espagueti', 'creador_username': 'vicenta', 'titulo': 'Fontana di Trevi y gelato',
         'descripcion': 'Tirar moneda y comer el mejor gelato', 'fecha_hora': '2025-09-12 16:00:00',
         'ubicacion': 'Fontana di Trevi', 'prioridad': 'MEDIA', 'categoria': 'CULTURAL', 'coste_estimado': 8},

        # Hawaii que Guay
        {'viaje_nombre': 'Hawaii que Guay', 'creador_username': 'juan', 'titulo': 'Surf en Waikiki Beach',
         'descripcion': 'Clases de surf en la playa más famosa', 'fecha_hora': '2025-06-12 08:00:00',
         'ubicacion': 'Waikiki Beach', 'prioridad': 'ALTA', 'categoria': 'AVENTURA', 'coste_estimado': 75},
        {'viaje_nombre': 'Hawaii que Guay', 'creador_username': 'juan', 'titulo': 'Luau hawaiano',
         'descripcion': 'Fiesta tradicional con comida y bailes', 'fecha_hora': '2025-06-15 19:00:00',
         'ubicacion': 'Polynesian Cultural Center', 'prioridad': 'MEDIA', 'categoria': 'CULTURAL',
         'coste_estimado': 95},
        {'viaje_nombre': 'Hawaii que Guay', 'creador_username': 'juan', 'titulo': 'Snorkel en Hanauma Bay',
         'descripcion': 'Buceo con peces tropicales', 'fecha_hora': '2025-06-18 10:00:00', 'ubicacion': 'Hanauma Bay',
         'prioridad': 'ALTA', 'categoria': 'AVENTURA', 'coste_estimado': 25},

        # Viva Las Vegas
        {'viaje_nombre': 'Viva Las Vegas', 'creador_username': 'paloma', 'titulo': 'Show del Cirque du Soleil',
         'descripcion': 'Espectáculo "O" en el Bellagio', 'fecha_hora': '2025-07-12 21:30:00',
         'ubicacion': 'Bellagio Hotel', 'prioridad': 'ALTA', 'categoria': 'OTROS', 'coste_estimado': 150},
        {'viaje_nombre': 'Viva Las Vegas', 'creador_username': 'paloma', 'titulo': 'Buffet en Caesars Palace',
         'descripcion': 'El famoso buffet de Las Vegas', 'fecha_hora': '2025-07-13 13:00:00',
         'ubicacion': 'Caesars Palace', 'prioridad': 'MEDIA', 'categoria': 'GASTRONOMIA', 'coste_estimado': 65},
        {'viaje_nombre': 'Viva Las Vegas', 'creador_username': 'paloma', 'titulo': 'Noche en los casinos',
         'descripcion': 'Probar suerte en blackjack y ruleta', 'fecha_hora': '2025-07-14 23:00:00',
         'ubicacion': 'The Strip', 'prioridad': 'BAJA', 'categoria': 'OTROS', 'coste_estimado': 100},

        # Paella por Marbella
        {'viaje_nombre': 'Paella por Marbella', 'creador_username': 'emilio', 'titulo': 'Playa de la Fontanilla',
         'descripcion': 'Día de relax en la playa', 'fecha_hora': '2025-08-11 11:00:00',
         'ubicacion': 'Playa de la Fontanilla', 'prioridad': 'ALTA', 'categoria': 'RELAX', 'coste_estimado': 15},
        {'viaje_nombre': 'Paella por Marbella', 'creador_username': 'emilio', 'titulo': 'Paella en chiringuito',
         'descripcion': 'La auténtica paella valenciana frente al mar', 'fecha_hora': '2025-08-12 14:00:00',
         'ubicacion': 'Chiringuito El Faro', 'prioridad': 'ALTA', 'categoria': 'GASTRONOMIA', 'coste_estimado': 35},
        {'viaje_nombre': 'Paella por Marbella', 'creador_username': 'emilio', 'titulo': 'Casco antiguo de Marbella',
         'descripcion': 'Paseo por las calles blancas andaluzas', 'fecha_hora': '2025-08-13 18:00:00',
         'ubicacion': 'Casco Antiguo', 'prioridad': 'MEDIA', 'categoria': 'CULTURAL', 'coste_estimado': 0},

        # DisneyLand París
        {'viaje_nombre': 'Disneyland París', 'creador_username': 'mariano', 'titulo': 'Space Mountain',
         'descripcion': 'La montaña rusa más épica de Disney', 'fecha_hora': '2025-06-08 10:00:00',
         'ubicacion': 'Disneyland Park', 'prioridad': 'ALTA', 'categoria': 'AVENTURA', 'coste_estimado': 0},
        {'viaje_nombre': 'Disneyland París', 'creador_username': 'mariano', 'titulo': 'Desfile de princesas',
         'descripcion': 'El mágico desfile de Disney', 'fecha_hora': '2025-06-09 15:00:00', 'ubicacion': 'Main Street',
         'prioridad': 'MEDIA', 'categoria': 'OTROS', 'coste_estimado': 0},
        {'viaje_nombre': 'Disneyland París', 'creador_username': 'mariano', 'titulo': 'Cena con Mickey Mouse',
         'descripcion': 'Cena temática con personajes Disney', 'fecha_hora': '2025-06-10 19:00:00',
         'ubicacion': 'Plaza Gardens Restaurant', 'prioridad': 'ALTA', 'categoria': 'GASTRONOMIA',
         'coste_estimado': 55},

        # No me mola ir a Londres sola
        {'viaje_nombre': 'No me mola ir a Londres sola', 'creador_username': 'isabel', 'titulo': 'Torre de Londres',
         'descripcion': 'Ver las joyas de la corona', 'fecha_hora': '2025-11-21 10:00:00',
         'ubicacion': 'Tower of London', 'prioridad': 'ALTA', 'categoria': 'CULTURAL', 'coste_estimado': 29.90},
        {'viaje_nombre': 'No me mola ir a Londres sola', 'creador_username': 'isabel',
         'titulo': 'Afternoon tea en Harrods', 'descripcion': 'Té de la tarde súper posh',
         'fecha_hora': '2025-11-22 16:00:00', 'ubicacion': 'Harrods', 'prioridad': 'MEDIA', 'categoria': 'GASTRONOMIA',
         'coste_estimado': 45},
        {'viaje_nombre': 'No me mola ir a Londres sola', 'creador_username': 'isabel', 'titulo': 'Musical en West End',
         'descripcion': 'Ver El Rey León en el teatro', 'fecha_hora': '2025-11-23 20:00:00',
         'ubicacion': 'Lyceum Theatre', 'prioridad': 'ALTA', 'categoria': 'OTROS', 'coste_estimado': 85},

        # Grecia con Gracia
        {'viaje_nombre': 'Grecia con Gracia', 'creador_username': 'marisa', 'titulo': 'Atardecer en Oia',
         'descripcion': 'El atardecer más bonito del mundo', 'fecha_hora': '2025-08-13 20:30:00',
         'ubicacion': 'Oia, Santorini', 'prioridad': 'ALTA', 'categoria': 'RELAX', 'coste_estimado': 0},
        {'viaje_nombre': 'Grecia con Gracia', 'creador_username': 'marisa', 'titulo': 'Degustación de vinos',
         'descripcion': 'Cata de vinos volcánicos de Santorini', 'fecha_hora': '2025-08-14 17:00:00',
         'ubicacion': 'Santo Wines', 'prioridad': 'MEDIA', 'categoria': 'GASTRONOMIA', 'coste_estimado': 40},
        {'viaje_nombre': 'Grecia con Gracia', 'creador_username': 'marisa', 'titulo': 'Playa Roja',
         'descripcion': 'Bañarse en la famosa playa volcánica', 'fecha_hora': '2025-08-15 12:00:00',
         'ubicacion': 'Red Beach', 'prioridad': 'ALTA', 'categoria': 'RELAX', 'coste_estimado': 0},

        # Exploradores por Egipto
        {'viaje_nombre': 'Exploradores por Egipto', 'creador_username': 'marisa', 'titulo': 'Pirámides de Giza',
         'descripcion': 'Las 7 maravillas del mundo antiguo', 'fecha_hora': '2025-10-11 08:00:00', 'ubicacion': 'Giza',
         'prioridad': 'ALTA', 'categoria': 'CULTURAL', 'coste_estimado': 20},
        {'viaje_nombre': 'Exploradores por Egipto', 'creador_username': 'marisa', 'titulo': 'Paseo en camello',
         'descripcion': 'Experiencia auténtica del desierto', 'fecha_hora': '2025-10-12 16:00:00',
         'ubicacion': 'Desierto de Sahara', 'prioridad': 'MEDIA', 'categoria': 'AVENTURA', 'coste_estimado': 35},
        {'viaje_nombre': 'Exploradores por Egipto', 'creador_username': 'marisa', 'titulo': 'Museo Egipcio',
         'descripcion': 'Tesoros de Tutankamón', 'fecha_hora': '2025-10-13 10:00:00',
         'ubicacion': 'Museo Egipcio de El Cairo', 'prioridad': 'ALTA', 'categoria': 'CULTURAL', 'coste_estimado': 12},
    ]

    for actividad_data in actividades_data:
        viaje = Viaje.objects.get(nombre=actividad_data['viaje_nombre'])
        creador = UsuarioPersonalizado.objects.get(username=actividad_data['creador_username'])

        Actividad.objects.create(
            viaje=viaje,
            creador=creador,
            titulo=actividad_data['titulo'],
            descripcion=actividad_data['descripcion'],
            fecha_hora=actividad_data['fecha_hora'],
            ubicacion=actividad_data['ubicacion'],
            prioridad=actividad_data['prioridad'],
            categoria=actividad_data['categoria'],
            coste_estimado=actividad_data['coste_estimado']
        )


def poblar_gastos(apps, schema_editor):
    Gasto = apps.get_model('viajes', 'Gasto')
    Viaje = apps.get_model('viajes', 'Viaje')
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')

    gastos_data = [
        # Japón con Jamón
        {'viaje_nombre': 'Japón con Jamón', 'pagador_username': 'emilio', 'cantidad': 120.50,
         'descripcion': 'Hotel en Shibuya - 2 noches', 'categoria': 'ALOJAMIENTO'},
        {'viaje_nombre': 'Japón con Jamón', 'pagador_username': 'emilio', 'cantidad': 85.30,
         'descripcion': 'Cena en restaurante de ramen', 'categoria': 'COMIDA'},
        {'viaje_nombre': 'Japón con Jamón', 'pagador_username': 'emilio', 'cantidad': 25.00,
         'descripcion': 'Metro pass semanal', 'categoria': 'TRANSPORTE'},

        # Aventuras por Edimburgo
        {'viaje_nombre': 'Aventuras por Edimburgo', 'pagador_username': 'belen', 'cantidad': 95.00,
         'descripcion': 'Hostel en Old Town', 'categoria': 'ALOJAMIENTO'},
        {'viaje_nombre': 'Aventuras por Edimburgo', 'pagador_username': 'belen', 'cantidad': 42.75,
         'descripcion': 'Fish and chips + whisky', 'categoria': 'COMIDA'},

        # Ruta Espagueti
        {'viaje_nombre': 'Ruta Espagueti', 'pagador_username': 'vicenta', 'cantidad': 78.00,
         'descripcion': 'Apartamento cerca del Vaticano', 'categoria': 'ALOJAMIENTO'},
        {'viaje_nombre': 'Ruta Espagueti', 'pagador_username': 'vicenta', 'cantidad': 56.20,
         'descripcion': 'Cena romántica con vista al Coliseo', 'categoria': 'COMIDA'},
        {'viaje_nombre': 'Ruta Espagueti', 'pagador_username': 'vicenta', 'cantidad': 16.00,
         'descripcion': 'Entradas Coliseo', 'categoria': 'ACTIVIDADES'},

        # Hawaii que Guay
        {'viaje_nombre': 'Hawaii que Guay', 'pagador_username': 'juan', 'cantidad': 250.00,
         'descripcion': 'Resort frente al mar', 'categoria': 'ALOJAMIENTO'},
        {'viaje_nombre': 'Hawaii que Guay', 'pagador_username': 'juan', 'cantidad': 75.00,
         'descripcion': 'Clases de surf', 'categoria': 'ACTIVIDADES'},
        {'viaje_nombre': 'Hawaii que Guay', 'pagador_username': 'juan', 'cantidad': 45.80,
         'descripcion': 'Poke bowl y smoothies', 'categoria': 'COMIDA'},

        # Viva Las Vegas
        {'viaje_nombre': 'Viva Las Vegas', 'pagador_username': 'paloma', 'cantidad': 180.00,
         'descripcion': 'Suite en el Strip', 'categoria': 'ALOJAMIENTO'},
        {'viaje_nombre': 'Viva Las Vegas', 'pagador_username': 'paloma', 'cantidad': 150.00,
         'descripcion': 'Show Cirque du Soleil', 'categoria': 'ACTIVIDADES'},
        {'viaje_nombre': 'Viva Las Vegas', 'pagador_username': 'paloma', 'cantidad': 65.00,
         'descripcion': 'Buffet Caesars Palace', 'categoria': 'COMIDA'},
        {'viaje_nombre': 'Viva Las Vegas', 'pagador_username': 'paloma', 'cantidad': 200.00,
         'descripcion': 'Perdidas en el casino (ups)', 'categoria': 'OTROS'},
    ]

    from datetime import date
    for gasto_data in gastos_data:
        viaje = Viaje.objects.get(nombre=gasto_data['viaje_nombre'])
        pagador = UsuarioPersonalizado.objects.get(username=gasto_data['pagador_username'])

        Gasto.objects.create(
            viaje=viaje,
            pagador=pagador,
            cantidad=gasto_data['cantidad'],
            descripcion=gasto_data['descripcion'],
            categoria=gasto_data['categoria'],
            fecha=date.today()
        )


def reverse_poblar_actividades(apps, schema_editor):
    Actividad = apps.get_model('viajes', 'Actividad')
    Actividad.objects.all().delete()


def reverse_poblar_gastos(apps, schema_editor):
    Gasto = apps.get_model('viajes', 'Gasto')
    Gasto.objects.all().delete()


def reverse_poblar_destinos(apps, schema_editor):
    Destino = apps.get_model('viajes', 'Destino')
    Destino.objects.all().delete()


def reverse_poblar_usuarios(apps, schema_editor):
    UsuarioPersonalizado = apps.get_model('viajes', 'UsuarioPersonalizado')
    UsuarioPersonalizado.objects.all().delete()


def reverse_poblar_viajes(apps, schema_editor):
    Viaje = apps.get_model('viajes', 'Viaje')
    Viaje.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('viajes', '0008_alter_megusta_unique_together_megusta_viaje_and_more'),
    ]

    operations = [
        migrations.RunPython(poblar_destinos, reverse_poblar_destinos),
        migrations.RunPython(poblar_usuarios, reverse_poblar_usuarios),
        migrations.RunPython(poblar_viajes, reverse_poblar_viajes),
        migrations.RunPython(poblar_actividades, reverse_poblar_actividades),
        migrations.RunPython(poblar_gastos, reverse_poblar_gastos),
    ]