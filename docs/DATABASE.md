# Base de datos (MySQL 8)

Garage360 usa **MySQL 8.x** (probado con 8.4) con codificación `utf8mb4`. Django crea y versiona las tablas mediante migraciones; [`database/schema.sql`](../database/schema.sql) es una exportación del esquema resultante, útil para revisar o crear la base sin Django.

## Preparar MySQL

```bash
mysql -u root -p < database/init.sql      # crea la base `garage360` y el usuario de la app
python manage.py migrate                   # crea las tablas
python manage.py seed --demo               # opcional: datos de ejemplo
```

`database/init.sql` crea la base con `utf8mb4_unicode_ci`, el usuario `garage360` y los permisos necesarios (incluida la base `test_garage360` que Django crea al ejecutar los tests).

## Variables de conexión

| Variable | Por defecto |
|---|---|
| `DB_ENGINE` | `mysql` |
| `DB_NAME` | `garage360` |
| `DB_HOST` / `DB_PORT` | `127.0.0.1` / `3306` |
| `DB_USER` / `DB_PASSWORD` | `garage360` / `garage360_dev` |

Cambia la contraseña en cualquier entorno que no sea tu máquina local.

## Driver

El proyecto usa **PyMySQL** (puro Python, no requiere compilar ni instalar librerías del sistema). Si tienes `mysqlclient` instalado, se usa automáticamente (más rápido). Ver [`garage360/__init__.py`](../garage360/__init__.py).

## Modelo relacional

El diagrama entidad-relación está en [ARCHITECTURE.md](ARCHITECTURE.md#modelo-de-datos). Tablas principales (prefijo `core_`):

| Tabla | Contenido |
|---|---|
| `core_usuariocustom` | Usuarios (extiende `AbstractUser`) con RUN, comuna y rol |
| `core_rolusuario` | Cliente · Encargado taller · Administrador |
| `core_region` / `core_comuna` | Geografía |
| `core_taller` | Talleres con coordenadas y encargado |
| `core_vehiculo` / `core_marca` / `core_tipovehiculo` | Vehículos de los clientes |
| `core_agenda` / `core_tipoagenda` / `core_estadoagenda` | Reservas, servicios y estados |
| `core_reportepago` | Monto y detalle de una reparación (1 a 1 con la reserva) |
| `core_ticket` / `core_estadoticket` | Solicitudes de encargados a administradores |
| `core_contacto` | Mensajes del formulario de contacto |

Integridad: todas las relaciones usan claves foráneas InnoDB; la reserva no admite dos citas a la misma hora en un taller (validado en la aplicación) y cada reserva tiene como máximo un reporte de pago.

## Respaldo y restauración

```bash
mysqldump -u garage360 -p --single-transaction garage360 > respaldo.sql
mysql -u garage360 -p garage360 < respaldo.sql
```

## Modo SQLite (solo desarrollo)

Para probar sin instalar MySQL: `DB_ENGINE=sqlite python manage.py migrate`. No se recomienda fuera de desarrollo; el CI ejecuta los tests en ambos motores.
