# Política de seguridad

## Reportar una vulnerabilidad

Si encuentras un problema de seguridad, **no abras un issue público**. Usa la pestaña *Security → Report a vulnerability* de este repositorio (reporte privado). Responderemos lo antes posible.

## Buenas prácticas del proyecto

- Ningún secreto en el código: `DJANGO_SECRET_KEY`, claves API y credenciales de base de datos se leen de variables de entorno. Con `DEBUG=False` la aplicación se niega a arrancar sin `DJANGO_SECRET_KEY`.
- Control de acceso por rol y por propietario en cada vista; la API filtra los datos por usuario.
- Acciones destructivas solo por `POST` con protección CSRF.
- Cookies de sesión y CSRF `Secure` cuando `DEBUG=False`.
- Las cuentas creadas por `seed --demo` usan una clave pública conocida: **no ejecutes `--demo` en producción**.

## Si desplegaste una versión anterior (FixSpot)

El repositorio original incluía claves y datos de usuarios en su historial. Ese historial fue reescrito, pero debes asumir que las claves antiguas están comprometidas: revócalas y cambia `SECRET_KEY` y las contraseñas de base de datos.
