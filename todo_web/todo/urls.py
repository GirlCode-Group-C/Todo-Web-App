from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_page, name="home"),
    path("create-todo/", views.create_todo, name="create_todo"),
    path("schedule/", views.schedule_todo, name="schedule_todo"),
]
