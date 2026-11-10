# Cómo contribuir

¡Gracias por querer mejorar TallerYa!

## Entorno de desarrollo

```bash
git clone https://github.com/nibrill/tallerya.git
cd tallerya
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed --demo
python manage.py runserver
```

## Flujo de trabajo

1. Haz un *fork* y crea una rama: `git checkout -b feat/mi-mejora`.
2. Escribe código y **tests** para lo que cambies.
3. Verifica: `python manage.py check && python manage.py test`.
4. Si cambias modelos: `python manage.py makemigrations` y sube la migración.
5. Abre un *pull request* describiendo el cambio (usa la plantilla).

## Convenciones

- Python: PEP 8, nombres en español para el dominio (como el resto del código), líneas de hasta ~120 caracteres.
- Commits: mensajes cortos en imperativo (`Agrega filtro por comuna`).
- No incluyas secretos, bases de datos ni archivos subidos por usuarios.
- Acciones que modifican datos: solo `POST` y con verificación de rol/propiedad.

## Capturas de pantalla

Si cambias la interfaz, regenera las capturas con `scripts/capture_screenshots.py` (instrucciones en el archivo).
