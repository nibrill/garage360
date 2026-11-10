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

# (archivo, usuario o None, ruta, esperar selector opcional, página completa, tema)
DESKTOP = [
    ('01-inicio', None, '/', None, True, 'dark'),
    ('02-inicio-claro', None, '/', None, True, 'light'),
    ('03-login', None, '/accounts/login/', None, False, 'dark'),
    ('04-registro', None, '/register/', None, False, 'dark'),
    ('05-talleres', 'cliente', '/talleres/', None, False, 'dark'),
    ('06-mapa', 'cliente', '/mapa/', '.leaflet-marker-icon', False, 'dark'),
    ('07-reservar-hora', 'cliente', '/agendar_hora/1/', None, False, 'dark'),
    ('08-mis-reservas', 'cliente', '/mis_reservas/', None, False, 'dark'),
    ('09-pago', 'cliente', '/detalle_reserva/2/', None, False, 'dark'),
    ('10-mis-vehiculos', 'cliente', '/mis_vehiculos/', None, False, 'dark'),
    ('11-panel-encargado', 'encargado1', '/reservas_taller/1/', None, False, 'dark'),
    ('12-panel-admin', 'admin', '/administracion/', None, False, 'dark'),
    ('13-admin-talleres', 'admin', '/administrar_talleres/', None, False, 'dark'),
    ('14-talleres-claro', 'cliente', '/talleres/', None, False, 'light'),
]
MOBILE = [('m1-inicio', None, '/', 'dark'), ('m2-talleres', 'cliente', '/talleres/', 'dark'),
          ('m3-mapa', 'cliente', '/mapa/', 'dark')]

SCROLL_JS = """async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 400) {
        window.scrollTo({ top: y, behavior: 'instant' });
        await new Promise(r => setTimeout(r, 70));
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
}"""


def new_context(browser, theme, **kw):
    ctx = browser.new_context(color_scheme=theme, **kw)
    ctx.add_init_script(f"try{{localStorage.setItem('g360-theme','{theme}')}}catch(e){{}}")
    return ctx


def login(context, usuario):
    page = context.new_page()
    page.goto(f'{BASE}/accounts/login/')
    page.fill('input[name=username]', usuario)
    page.fill('input[name=password]', PASSWORD)
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')
    page.close()


def shot(browser, nombre, usuario, ruta, esperar, completa, tema, **ctx_kw):
    ctx = new_context(browser, tema, **ctx_kw)
    if usuario:
        login(ctx, usuario)
    page = ctx.new_page()
    page.goto(BASE + ruta)
    page.wait_for_load_state('networkidle')
    if esperar:
        page.wait_for_selector(esperar, timeout=15000)
        page.wait_for_timeout(2500)  # teselas del mapa
    page.evaluate(SCROLL_JS)  # dispara las animaciones de entrada
    page.wait_for_timeout(1400)
    page.screenshot(path=str(OUT / f'{nombre}.png'), full_page=completa)
    print('ok', nombre)
    ctx.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    channel = os.environ.get('BROWSER_CHANNEL') or None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel)
        for nombre, usuario, ruta, esperar, completa, tema in DESKTOP:
            shot(browser, nombre, usuario, ruta, esperar, completa, tema,
                 viewport={'width': 1366, 'height': 820})
        for nombre, usuario, ruta, tema in MOBILE:
            shot(browser, nombre, usuario, ruta, '.leaflet-marker-icon' if 'mapa' in ruta else None, False, tema,
                 viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        browser.close()


if __name__ == '__main__':
    main()
