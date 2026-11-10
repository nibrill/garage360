"""Genera las capturas de pantalla de docs/screenshots usando Playwright.

Uso (con el servidor corriendo y datos demo cargados):

    pip install playwright && playwright install chromium
    python manage.py migrate && python manage.py seed --demo
    python manage.py runserver 8765
    python scripts/capture_screenshots.py http://127.0.0.1:8765

Por defecto usa Chromium; define BROWSER_CHANNEL=msedge (o chrome) para usar un navegador ya instalado.
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765').rstrip('/')
OUT = Path(__file__).resolve().parent.parent / 'docs' / 'screenshots'
PASSWORD = 'garage360123'  # clave de las cuentas creadas por `seed --demo`

# (archivo, usuario o None, ruta, esperar selector opcional, página completa)
DESKTOP = [
    ('01-inicio', None, '/', None, True),
    ('02-login', None, '/accounts/login/', None, False),
    ('03-talleres', 'cliente', '/talleres/', None, True),
    ('04-mapa', 'cliente', '/mapa/', '.leaflet-marker-icon', False),
    ('05-reservar-hora', 'cliente', '/agendar_hora/1/', None, True),
    ('06-mis-reservas', 'cliente', '/mis_reservas/', None, False),
    ('07-mis-vehiculos', 'cliente', '/mis_vehiculos/', None, False),
    ('08-panel-encargado', 'encargado1', '/reservas_taller/1/', None, False),
    ('09-panel-admin', 'admin', '/administracion/', None, False),
    ('10-admin-talleres', 'admin', '/administrar_talleres/', None, False),
]
MOBILE = [('m1-inicio', None, '/'), ('m2-talleres', 'cliente', '/talleres/')]


def login(context, usuario):
    page = context.new_page()
    page.goto(f'{BASE}/accounts/login/')
    page.fill('input[name=username]', usuario)
    page.fill('input[name=password]', PASSWORD)
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')
    page.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    channel = os.environ.get('BROWSER_CHANNEL') or None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel)
        for nombre, usuario, ruta, esperar, completa in DESKTOP:
            ctx = browser.new_context(viewport={'width': 1366, 'height': 820}, device_scale_factor=1)
            if usuario:
                login(ctx, usuario)
            page = ctx.new_page()
            page.goto(BASE + ruta)
            page.wait_for_load_state('networkidle')
            if esperar:
                page.wait_for_selector(esperar, timeout=15000)
                page.wait_for_timeout(2500)  # teselas del mapa
            page.screenshot(path=str(OUT / f'{nombre}.png'), full_page=completa)
            print('ok', nombre)
            ctx.close()
        for nombre, usuario, ruta in MOBILE:
            ctx = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                      is_mobile=True, has_touch=True)
            if usuario:
                login(ctx, usuario)
            page = ctx.new_page()
            page.goto(BASE + ruta)
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(OUT / f'{nombre}.png'), full_page=False)
            print('ok', nombre)
            ctx.close()
        browser.close()


if __name__ == '__main__':
    main()
