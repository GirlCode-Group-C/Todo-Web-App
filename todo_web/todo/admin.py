from django.contrib import admin
from .models import Todo
from .models import TodoType

admin.site.register(Todo)
admin.site.register(TodoType)
# Register your models here.
