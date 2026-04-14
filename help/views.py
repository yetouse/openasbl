from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from help.context import get_help_text


@login_required
def help_panel(request):
    topic = request.GET.get("topic", "")
    text = get_help_text(topic)
    return render(request, "help/help_panel.html", {"topic": topic, "text": text})
