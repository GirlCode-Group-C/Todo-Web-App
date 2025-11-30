from django.contrib import admin
from .models import TaskTemplate, Todo
from .models import Todos
from .models import TodoType

admin.site.register(Todos)
admin.site.register(TodoType)
admin.site.register(TaskTemplate)
admin.site.register(Todo)
