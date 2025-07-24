from django import template

register = template.Library()

@register.filter
def percentage_width(value):
    """Convert a 0-10 value to a percentage width (0-100)"""
    try:
        return float(value) * 10
    except (ValueError, TypeError):
        return 0
