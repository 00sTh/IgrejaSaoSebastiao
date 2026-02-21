from django import template

register = template.Library()


@register.filter(name="split")
def split_string(value, delimiter="|"):
    """Split a string by delimiter. Usage: {{ value|split:"|" }}"""
    if not value:
        return []
    return value.split(delimiter)
