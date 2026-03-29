from django.http import Http404
from django.shortcuts import render

from .constants import MODULES


def home(request):
    return render(
        request,
        "dashboard/home.html",
        {
            "nav_active": "home",
        },
    )


def module_page(request, module_key):
    if module_key not in MODULES:
        raise Http404("Unknown module")
    return render(
        request,
        "dashboard/module.html",
        {
            "nav_active": module_key,
            "module": MODULES[module_key],
            "module_key": module_key,
        },
    )
