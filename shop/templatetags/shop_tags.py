from django import template

register = template.Library()


@register.filter
def sizes(value):
    return value.split(",")


@register.filter
def money(value):
    return f"{int(value):,}".replace(",", ".") + " ₫"
