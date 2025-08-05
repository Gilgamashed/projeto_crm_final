from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def build_query(**kwargs):
    """
    Constrói uma string de query URL mantendo os filtros atuais
    Exemplo: href="?{% build_query status='active' prioridade='alta' %}"
    """
    # Remove valores vazios
    params = {k: v for k, v in kwargs.items() if v not in [None, '']}
    return urlencode(params)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')