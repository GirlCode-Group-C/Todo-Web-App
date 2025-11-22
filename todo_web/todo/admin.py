from django.contrib import admin
from .models import Todos
from .models import TodoType

admin.site.register(Todos)
admin.site.register(TodoType)
# Register your models here.
