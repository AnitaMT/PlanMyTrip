## PlanMyTrip

PlanMyTrip es tu compañero digital para organizar viajes en grupo de forma sencilla y divertida. Desde la planificación de itinerarios hasta la gestión de gastos, pasando por un chat asistido por IA, esta aplicación cubre cada detalle para que solo te preocupes de disfrutar.

---

### Características destacadas

#### Gestión de usuarios

* Registro y autenticación seguras.
* Perfil personalizable con foto.
* Gestión de amigos: solicitudes, aceptaciones y listas.

#### Creación y colaboración en viajes

* Crear viajes con nombre, fechas, destino e imagen.
* Invitar y añadir colaboradores.
* Dashboard con estado "Activo" o "Finalizado".
* Visibilidad pública o privada.

#### Itinerarios y actividades

* CRUD completo de actividades con:

  * Título, descripción y fecha/hora.
  * Ubicación georreferenciada.
  * Prioridad y categoría.
  * Coste estimado para facilitar el presupuesto.
  * Likes y comentarios en cada actividad.

#### Gestión de gastos y deudas

* Registrar gastos con categoría, pudiendo añadir también comprobante.
* División automática del coste entre participantes.
* Seguimiento de deudas y notificaciones de pagos.
* Resumen de deudas total y detalles de los gastos.

#### Notificaciones y chat de asistencia

* Notificaciones en tiempo real (nuevos gastos, actividades, solicitudes).
* Opción arcar como leídas y borrarlas.
* Chat integrado con IA (Google Gemini) para resolver dudas y aceptar sugerencias.

#### Sugerencias inteligentes y mapas

* Recomendaciones de lugares y actividades basadas en IA.
* Búsqueda de POIs (puntos de interés) con Overpass (OpenStreetMap) y Mapbox.
* Viajes públicos con filtros por destino, continente, popularidad y grupos reducidos.

#### API REST

* Endpoint de gastos por categoría para integrar gráficas.
* Documentación automática con Swagger/DRF-Spectacular.

---

## Estructura del proyecto

```bash
PlanMyTrip/                # Raíz del repositorio
├── PlanMyTrip/            # Configuración global de Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── viajes/                # App principal
│   ├── migrations/        # Migraciones
│   ├── models.py          # Definición de entidades
│   ├── views.py           # Vistas basadas en clases y funciones auxiliares
│   ├── forms.py           # Formularios personalizados
│   ├── tests.py           # Pruebas automatizadas
│   ├── urls.py            # Rutas específicas
│   └── templates/viajes/  # Plantillas HTML y fragmentos (Bootstrap)
├── static/                # CSS, JS, imágenes estáticas
├── media/                 # Archivos subidos por usuarios
├── Dockerfile             # Dockerfiles de despliegue
├── requirements.txt       # Dependencias Python
├── docker-compose.yml     # Configuración de servicios (PostgreSQL, Redis, etc.)
├── manage.py              # Comandos de Django
└── README.md              # Documentación del proyecto
```

---

## Medios utilizados

1. **Frontend**: Plantillas Django + Bootstrap + AJAX para peticiones dinámicas.
2. **Backend**: Django MVC, vistas basadas en clases y DRF para endpoints REST.
3. **Base de datos**: PostgreSQL para datos relacionales y almacenamiento de datos.
4. **IA/Web APIs**:

   * Google Gemini: chat asistido y sugerencias inteligentes.
   * OpenStreetMap Overpass: puntos de interés.
   * Mapbox: visualización de mapas y geocodificación.
5. **Despliegue**: Docker + Docker Compose, con uso de AWS.

---

## Principales componentes

### Modelos

| Nombre del modelo    | Relaciones principales                                            |
| -------------------- | ----------------------------------------------------------------- |
| UsuarioPersonalizado | amigos (M2M a sí mismo), permisos (M2M)                           |
| Destino              | viajes (1 a N)                                                    |
| Viaje                | destino (FK), colaboradores (M2M), creador (FK)                   |
| Actividad            | viaje (FK), creador (FK), comentarios (1 a N), me\_gustas (1 a N) |
| Comentario           | actividad (FK), autor (FK)                                        |
| MeGusta              | actividad (FK opcional), viaje (FK opcional), usuario (FK)        |
| Gasto                | viaje (FK), pagador (FK), divisiones (1 a N)                      |
| DivisionGasto        | gasto (FK), deudor (FK)                                           |
| Notificacion         | usuario (FK)                                                      |
| SugerenciaIA         | destino (FK), viaje (FK), usuario (FK)                            |
| SolicitudAmistad     | emisor (FK), receptor (FK)                                        |

### Vistas

| Nombre de la vista                                                                                 | Descripción breve                                |
|----------------------------------------------------------------------------------------------------| ------------------------------------------------ |
| IndexView                                                                                          | Página de bienvenida                             |
| RegistroUsuarioView                                                                                | Formulario de registro de nuevos usuarios        |
| UsuarioLoginView / Logout                                                                          | Login y logout con mensajes personalizados       |
| PaginaInicioUsuarioView                                                                            | Dashboard de usuario con viajes y notificaciones |
| CrearViajeView                                                                                     | Creación de un nuevo viaje                       |
| DetallesViajeView                                                                                  | Detalles de viaje: actividades, gastos y IA      |
| EditarViajeView / EliminarViajeView                                                                | Edición y eliminación de viajes                  |
| AgregarColaboradorView / EliminarColaboradorView                                                   | Gestión de colaboradores                         |
| AgregarActividadView / EditarActividadView / EliminarActividadView                                 | CRUD actividades                                 |
| AgregarGastoView / EliminarGastoView                                                               | Registro y gestión de gastos                     |
| LikeToggleView / ActividadLikesView                                                                | Likes en actividades                             |
| ToggleLikeViajeView / ViajeLikesView                                                               | Likes en viajes                                  |
| ViajesPublicosView                                                                                 | Listado y filtros de viajes públicos             |
| NotificacionRedirectView / NotificacionListView / MarcarTodasLeidasView / EliminarNotificacionView | Gestión de notificaciones                        |
| GastosPorCategoriaAPI                                                                              | API REST de gastos por categoría                 |

### Formularios

| Nombre del formulario | Descripción breve                                |
|-----------------------|--------------------------------------------------|
| RegistroUsuarioForm   | Registro de usuario con validación de contraseña |
| CrearViajeForm        | Crear un viaje con destino libre y categorías    |
| EditarViajeForm       | Editar detalles de viaje                         |
| AgregarActividadForm  | Añadir o editar actividades                      |
| FotoPerfilForm        | Actualizar foto de perfil                        |
| CambiarUsernameForm   | Cambiar nombre de usuario                        |
| CambiarPasswordForm   | Cambiar contraseña con validación estándar       |

### Tests

| Nombre del test             | Descripción breve                               |
|-----------------------------|-------------------------------------------------|
| IndexViewTest               | Acceso y renderizado de la página principal     |
| RegistroUsuarioViewTest     | Registro de usuarios y mensajes de confirmación |
| UsuarioLoginViewTest        | Login válido e inválido                         |
| PaginaInicioUsuarioViewTest | Dashboard: viajes y notificaciones              |
| CrearViajeViewTest          | Creación de viajes y destinos automáticos       |
| DetallesViajeViewTest       | Cálculo de deudas y renderizado de detalles     |
| AgregarColaboradorViewTest  | Añadir colaborador y notificación               |
| AgregarActividadViewTest    | CRUD de actividades                             |
| AgregarGastoViewTest        | Registro y división de gastos                   |
| LikeToggleViewTest          | Toggle de likes en actividad                    |
| ToggleLikeViajeViewTest     | Toggle de likes en viaje                        |

## Instalación y despliegue

### Requisitos

* Docker & Docker Compose
* Git
* Cuenta AWS

### Desarrollo local

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/tu-usuario/PlanMyTrip.git
   cd PlanMyTrip
   ```

2. Copiar y configurar variables de entorno en `.env`:

   ```ini
   POSTGRES_DB=planmytrip
   POSTGRES_USER=usuario
   POSTGRES_PASSWORD=contraseña
   MAPBOX_TOKEN=tu_mapbox_token
   GEMINI_API_KEY=tu_api_key
   ```

3. Levantar servicios:

   ```bash
   docker-compose up -d
   ```

4. Aplicar migraciones y crear superusuario:

   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

5. Acceder a la app en `http://localhost:8000/viajes/`.


## API Documentation

Después de arrancar el servidor, la documentación interactiva está disponible en:

```
http://localhost:8000/api/schema/   # Esquema OpenAPI
http://localhost:8000/api/docs/     # Swagger UI
```

### Ejemplo de endpoint: Gastos por categoría

```http
GET /api/viajes/{viaje_id}/gastos/
Host: api.planmytrip.com
Authorization: Token <your_token>
```

**Respuesta:**

```json
{
  "viaje_id": 1,
  "totales_por_categoria": [
    {"categoria": "COMIDA", "total": 250.50},
    {"categoria": "TRANSPORTE", "total": 120.00}
  ]
}
```

---

## Ejemplo de uso (Paso a paso)

1. **Registro**: Usuario se da de alta con email y contraseña.
2. **Crear viaje**:

   * Nombre: "Escapada Madrid"
   * Destino: "Madrid, España"
   * Fechas: 2025-07-10 a 2025-07-15
   * Visibilidad: Público
3. **Invitar amigos**:

   * Buscas usuarios por nombre.
   * Envías solicitudes de amistad; ellos aceptan.
4. **Planificar actividades**:

   * Añades actividad: "Visita al Prado", 2025-07-11 10:00, Categoría: CULTURAL.
   * Tus amigos dan like y comentan.
5. **Gestionar gastos**:

   * Registras gasto: 100€ en "Cena".
   * Divides entre 4 participantes.
   * Cada uno ve su deuda y marca como pagada al abonar.
6. **Chat de asistencia**:

   * Preguntas: "¿Dónde comer barato en Madrid?".
   * TravesIA responde con 3 recomendaciones y emojis.
7. **Explorar viajes públicos**:

   * Filtras por "Europa" o "grupos reducidos".
   * Te inspiras con itinerarios de otros.

---

## Próximas mejoras

* **WebSockets** para notificaciones en vivo y chat en tiempo real.
* **Dashboard con gráficos interactivos de actividades**, así como creación de APIs de interés para el usuario como tiempo de uso de pantalla o visualizaciones mensuales que ha tenido el perfil.
* **Celery** para recordatorios sobre deudas pendientes.
* Opción a **incluir fotos dentro del viaje** con el fin de que, al final del viaje, los usuarios tengan la opción de obtener un álbum de fotos del viaje que sería generado con IA.
* **Exportación de itinerarios a PDF con un formato más bonito**, incluyendo mapas y rutas.

---

