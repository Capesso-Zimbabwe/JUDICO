from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup a key in a dictionary"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []

@register.filter
def cut_spaces(value):
    """Remove all spaces from a string"""
    return str(value).replace(' ', '')