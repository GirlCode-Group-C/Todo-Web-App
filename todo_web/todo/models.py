from django.db import models


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
