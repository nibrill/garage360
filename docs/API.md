# API REST

Base: `/api/` (Django REST Framework). Se autentica con la sesión del navegador. Navega la API interactiva en `/api/` con la sesión iniciada.

| Endpoint | Métodos | Quién |
|---|---|---|
| `/api/roles/` `/api/regiones/` `/api/comunas/` `/api/marcas/` `/api/tipos-vehiculo/` `/api/tipos-agenda/` `/api/talleres/` | GET | Cualquier usuario con sesión |
| (los mismos) | POST/PUT/PATCH/DELETE | Solo administrador |
| `/api/usuarios/` | todos | Solo administrador (no expone contraseñas) |
| `/api/vehiculos/` | todos | Cada usuario solo ve y edita los suyos; el administrador ve todos |
| `/api/agendas/` | GET | Cliente: sus reservas · Encargado: las de su taller · Administrador: todas |

Otras rutas JSON usadas por la interfaz:

| Ruta | Descripción |
|---|---|
| `GET /get_available_hours/?date=YYYY-MM-DD&id_taller=N` | Horas libres de un taller |
| `GET /autocomplete_address/?term=...` | Sugerencias de direcciones |

## Ejemplo

```bash
curl -b cookies.txt http://127.0.0.1:8000/api/talleres/
```

Respuesta (resumen):

```json
[{"idTaller": 1, "nombreTaller": "Mecánica Express Providencia", "latitud": -33.426, "longitud": -70.618}]
```
