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

class TaskTemplate(models.Model):
    CATEGORY_CHOICES = [
        ("personal", "Personal"),
        ("school", "School"),
        ("work", "Work"),
    ]

    name = models.CharField(max_length=120)  # e.g. "Meeting with Sean"
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("name", "category")  # avoid duplicates

    def __str__(self):
        return f"{self.category.capitalize()} - {self.name}"


class Todo(models.Model):
    """
    This can be used later by the dashboard as scheduled tasks.
    For now, your page will only create TaskTemplate entries.
    """
    CATEGORY_CHOICES = [
        ("personal", "Personal"),
        ("school", "School"),
        ("work", "Work"),
    ]

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    # Optional link to template (not required right now)
    template = models.ForeignKey(
        TaskTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.category.capitalize()} - {self.title} ({self.date})"
