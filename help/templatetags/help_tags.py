from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def help_button(topic):
    return mark_safe(
        f'<button class="btn btn-outline-secondary btn-sm rounded-circle" '
        f'style="width: 28px; height: 28px; padding: 0; font-weight: bold; line-height: 1;" '
        f'hx-get="/help/panel/?topic={topic}" hx-target="#help-panel" hx-swap="innerHTML" '
        f'title="Aide">?</button>'
    )
