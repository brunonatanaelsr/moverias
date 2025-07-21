from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    """
    Adiciona uma classe CSS a um campo de formulário
    """
    if hasattr(value, 'widget'):
        # Se é um campo de formulário
        existing_classes = value.widget.attrs.get('class', '')
        if existing_classes:
            value.widget.attrs['class'] = f"{existing_classes} {css_class}"
        else:
            value.widget.attrs['class'] = css_class
    return value
