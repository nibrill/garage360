# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [2.0.0] - 2026-11-10

Renombrado de **FixSpot** a **TallerYa** y renovación completa.

### Agregado
- Nuevo diseño responsive, logo, favicon y metadatos SEO (Open Graph, `robots.txt`, `sitemap.xml`).
- Buscador de talleres por nombre y comuna; panel de administración con métricas.
- Comando `seed` (catálogos y datos de demostración).
- Suite de 21 tests y CI con GitHub Actions.
- Dockerfile, `docker-compose.yml` y `render.yaml`.
- Documentación: README, arquitectura, API, seguridad y guía de contribución.

### Cambiado
- SQLite por defecto; MySQL opcional vía variables de entorno.
- Geocodificación con OpenStreetMap si no hay clave de OpenCage.
- Se reemplazó `django-crispy-forms` por un parcial propio compatible con Django 6.

### Seguridad
- Secretos movidos a variables de entorno.
- Control de acceso por rol y propietario; acciones destructivas solo por `POST` + CSRF.
- La API ya no expone usuarios ni hashes de contraseña.
- Historial de git reescrito para eliminar claves y datos de usuarios.

### Corregido
- Rutas rotas, login duplicado, import faltante en horas disponibles, mapa centrado en España, doble reporte de pago, validación de correo dependiente de un servicio externo.

## [1.0.0] - 2024

Versión universitaria original (FixSpot).
