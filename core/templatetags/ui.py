from django import template

register = template.Library()


@register.filter
def add_class(field, css):
    """Agrega clases CSS al widget de un campo de formulario."""
    attrs = field.field.widget.attrs
    attrs['class'] = (attrs.get('class', '') + ' ' + css).strip()
    return field.as_widget()


@register.filter
def field_type(field):
    return field.field.widget.__class__.__name__


@register.filter
def estado_clase(nombre):
    """Clase de color Bootstrap según el nombre del estado."""
    n = (nombre or '').lower()
    if 'pagad' in n or 'acept' in n or 'complet' in n:
        return 'success'
    if 'rechaz' in n or 'cancel' in n:
        return 'danger'
    if 'pend' in n:
        return 'warning'
    return 'secondary'
