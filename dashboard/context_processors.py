from .constants import MODULES, NAV_SECTIONS


def dashboard_nav(_request):
    return {
        "modules": MODULES,
        "nav_sections": NAV_SECTIONS,
    }
