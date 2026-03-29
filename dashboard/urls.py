from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("module/<slug:module_key>/", views.module_page, name="module"),
]
