"""
Template tags para asset bundling
MoveMarias - Sistema de gerenciamento de assets
"""

import json
import os
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from pathlib import Path

register = template.Library()

# Cache para o manifest
_manifest_cache = None

def get_manifest():
    """Carrega o manifest de assets"""
    global _manifest_cache
    
    if _manifest_cache is None or settings.DEBUG:
        manifest_path = Path(settings.BASE_DIR) / 'static' / 'bundles' / 'manifest.json'
        
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                _manifest_cache = json.load(f)
        else:
            _manifest_cache = {}
    
    return _manifest_cache

@register.simple_tag
def bundle_css(bundle_name):
    """Retorna a tag CSS para um bundle"""
    manifest = get_manifest()
    key = f"css.{bundle_name}"
    
    if key in manifest:
        bundle_path = manifest[key]['path']
        return mark_safe(f'<link rel="stylesheet" href="{settings.STATIC_URL}{bundle_path}">')
    
    # Fallback para desenvolvimento
    return mark_safe(f'<!-- Bundle CSS "{bundle_name}" não encontrado -->')

@register.simple_tag
def bundle_js(bundle_name):
    """Retorna a tag JS para um bundle"""
    manifest = get_manifest()
    key = f"js.{bundle_name}"
    
    if key in manifest:
        bundle_path = manifest[key]['path']
        return mark_safe(f'<script src="{settings.STATIC_URL}{bundle_path}"></script>')
    
    # Fallback para desenvolvimento
    return mark_safe(f'<!-- Bundle JS "{bundle_name}" não encontrado -->')

@register.simple_tag
def bundle_url(bundle_type, bundle_name):
    """Retorna a URL de um bundle"""
    manifest = get_manifest()
    key = f"{bundle_type}.{bundle_name}"
    
    if key in manifest:
        bundle_path = manifest[key]['path']
        return f"{settings.STATIC_URL}{bundle_path}"
    
    return ""

@register.simple_tag
def bundle_info(bundle_type, bundle_name):
    """Retorna informações sobre um bundle"""
    manifest = get_manifest()
    key = f"{bundle_type}.{bundle_name}"
    
    if key in manifest:
        return manifest[key]
    
    return {}

@register.inclusion_tag('components/critical_css.html')
def critical_css():
    """Inclui CSS crítico inline"""
    return {}

@register.inclusion_tag('components/preload_assets.html')
def preload_assets(*bundle_names):
    """Gera preload links para assets"""
    manifest = get_manifest()
    assets = []
    
    for bundle_name in bundle_names:
        css_key = f"css.{bundle_name}"
        js_key = f"js.{bundle_name}"
        
        if css_key in manifest:
            assets.append({
                'url': f"{settings.STATIC_URL}{manifest[css_key]['path']}",
                'type': 'style'
            })
        
        if js_key in manifest:
            assets.append({
                'url': f"{settings.STATIC_URL}{manifest[js_key]['path']}",
                'type': 'script'
            })
    
    return {'assets': assets}

@register.simple_tag
def asset_version():
    """Retorna a versão dos assets baseada no timestamp"""
    manifest = get_manifest()
    
    if manifest:
        # Usa o hash do primeiro bundle como versão
        first_bundle = next(iter(manifest.values()), {})
        return first_bundle.get('hash', '1')
    
    return '1'
