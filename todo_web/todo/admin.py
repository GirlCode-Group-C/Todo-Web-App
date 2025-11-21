from django.contrib import admin
from .models import TaskTemplate, Todo


admin.site.register(TaskTemplate)
admin.site.register(Todo)
