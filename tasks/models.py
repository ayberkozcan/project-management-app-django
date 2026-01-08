from django.conf import settings
from django.db import models

from groups.models import Group
from projects.models import Project

User = settings.AUTH_USER_MODEL

class Task(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=500, blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    assignees = models.ManyToManyField(User, related_name="assigned_tasks", blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ("project", "name")