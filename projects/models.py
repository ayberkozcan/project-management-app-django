from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=500, blank=True)
    owner = models.ForeignKey(
        "accounts.Account", 
        on_delete=models.CASCADE, 
        related_name="owned_projects"
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

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="employee")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")