"""
URL configuration for todo_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from todo import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('get-todos-json/', views.get_todos_json, name='get_todos_json'),
    path('get-todo-json/<int:todo_id>/', views.get_todo_json, name='get_todo_json'),
    path('add-todo-from-calendar/', views.add_todo_from_calendar, name='add_todo_from_calendar'),
    path('update-todo/<int:id>/', views.update_todo, name='update_todo'),
    path('delete-todo/<int:id>/', views.delete_todo, name='delete_todo'),
    path('sidebar-partial/', views.sidebar_partial, name='sidebar_partial'),

]
