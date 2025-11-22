from django.db import models

class TodoType(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

class Todos(models.Model):
    todo_type = models.ForeignKey(TodoType, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

