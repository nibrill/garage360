"""Geocodificación: usa OpenCage si hay OPENCAGE_API_KEY, si no OpenStreetMap (Nominatim)."""
import requests
from django.conf import settings

USER_AGENT = 'TallerYa/1.0 (proyecto educativo; https://github.com/nibrill/tallerya)'
TIMEOUT = 8


def _en_region_metropolitana(estado):
    estado = (estado or '').lower()
    return 'metropolitan' in estado or 'metropolitana' in estado


def geocodificar(direccion):
    """Devuelve (coordenadas, error). coordenadas = {'lat':..,'lng':..} o None."""
    direccion = (direccion or '').strip()
    if not direccion:
        return None, 'Ingresa una dirección.'
    try:
        if settings.OPENCAGE_API_KEY:
            r = requests.get(
                'https://api.opencagedata.com/geocode/v1/json',
                params={'q': direccion, 'key': settings.OPENCAGE_API_KEY, 'countrycode': 'cl', 'limit': 1},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            resultados = r.json().get('results') or []
            if not resultados:
                return None, 'No se encontró la dirección.'
            geom = resultados[0]['geometry']
            estado = resultados[0].get('components', {}).get('state')
            coords = {'lat': geom['lat'], 'lng': geom['lng']}
        else:
            r = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params={'q': direccion, 'format': 'json', 'addressdetails': 1, 'limit': 1, 'countrycodes': 'cl'},
                headers={'User-Agent': USER_AGENT},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            resultados = r.json()
            if not resultados:
                return None, 'No se encontró la dirección.'
            estado = resultados[0].get('address', {}).get('state')
            coords = {'lat': float(resultados[0]['lat']), 'lng': float(resultados[0]['lon'])}
    except (requests.RequestException, ValueError, KeyError):
        return None, 'Error en la solicitud de geocodificación.'
    if not _en_region_metropolitana(estado):
        return None, 'La dirección seleccionada no está en la Región Metropolitana.'
    return coords, None


def sugerencias(termino):
    try:
        r = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': termino, 'format': 'json', 'limit': 5, 'countrycodes': 'cl'},
            headers={'User-Agent': USER_AGENT},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return [x['display_name'] for x in r.json()]
    except (requests.RequestException, ValueError, KeyError):
        return []
