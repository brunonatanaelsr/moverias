from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Adiciona uma classe CSS ao widget de um campo de formulário"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field
