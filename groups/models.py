from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Group(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(max_length=500, blank=True)
    members = models.ManyToManyField(
        User,
        related_name="custom_groups",
        blank=True
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_groups"
    )
    projects = models.ManyToManyField(
        "projects.Project",
        related_name="assigned_groups",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "owner")

    def __str__(self):
        return self.name
    
ROLE_CHOICES = [
    ("admin", "Admin"),
    ("employee", "Employee"),
]

class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_members")
    user = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="employee")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")