from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def help_button(topic):
    return mark_safe(
        f'<button class="btn" hx-get="/help/panel/?topic={topic}" hx-target="#help-panel" hx-swap="innerHTML" title="Aide">?</button>'
    )
