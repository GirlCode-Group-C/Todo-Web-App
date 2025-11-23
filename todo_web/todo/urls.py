from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_page, name="home"),
    path("create-todo/", views.create_todo, name="create_todo"),
    path("schedule/", views.schedule_todo, name="schedule_todo"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('get-todos-json/', views.get_todos_json, name='get_todos_json'),
    path('get-todo-json/<str:todo_id>/', views.get_todo_json, name='get_todo_json'),
    path('add-todo-from-calendar/', views.add_todo_from_calendar, name='add_todo_from_calendar'),
    path('update-todo/<int:id>/', views.update_todo, name='update_todo'),
    path('delete-todo/<int:id>/', views.delete_todo, name='delete-todo'),
    path('delete-todo-todo/<int:id>/', views.delete_todo_todo, name='delete_todo_todo'),
    path('update-todo-todo/<int:id>/', views.update_todo_todo, name='update_todo_todo'),
    path('sidebar-partial/', views.sidebar_partial, name='sidebar_partial'),
]
