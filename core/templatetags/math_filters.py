"""
Filtros personalizados para cálculos matemáticos
"""

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def mul(value, arg):
    """
    Multiplica um valor por um argumento
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """
    Divide um valor por um argumento
    """
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """
    Calcula a porcentagem de um valor em relação ao total
    """
    try:
        if float(total) == 0:
            return 0
        result = (float(value) / float(total)) * 100
        return round(result, 1)
    except (ValueError, TypeError):
        return 0


@register.filter
def add_float(value, arg):
    """
    Soma dois números com suporte a decimais
    """
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def sub(value, arg):
    """
    Subtrai um valor de outro
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value
