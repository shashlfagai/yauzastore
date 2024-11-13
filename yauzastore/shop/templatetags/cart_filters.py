from django import template
from django.template.defaulttags import register


register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_key(dictionary):
    return dictionary.keys()


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def total_cost(items):
    return sum(float(item['price']) * item['quantity'] for item in items)


@register.filter
def money_to_rub(money):
    return f"{money.amount}" if money else "0"


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
