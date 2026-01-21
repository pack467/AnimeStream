from django import template

register = template.Library()


@register.filter(name='split')
def split(value, arg=","):
    """
    Split a string by a delimiter
    Usage: {{ value|split:"," }}
    """
    if value is None:
        return []
    return [x.strip() for x in str(value).split(arg) if x.strip()]


@register.filter(name='trim')
def trim(value):
    """
    Remove leading and trailing whitespace
    Usage: {{ value|trim }}
    """
    if value is None:
        return ""
    return str(value).strip()