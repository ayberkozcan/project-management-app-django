from django.conf import settings
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=500, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
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


class Comment(models.Model):
    MAX_CONTENT_LENGTH = 200

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        related_name="comments",
        null=True,
        blank=True,
    )
    content = models.CharField(max_length=MAX_CONTENT_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} on {self.project}"


class ActivityLog(models.Model):
    ACTION_COMMENT = "comment"
    ACTION_TASK = "task"
    ACTION_MEMBER = "member"
    ACTION_GROUP = "group"
    ACTION_PROJECT = "project"

    ACTION_CHOICES = [
        (ACTION_COMMENT, "Comment"),
        (ACTION_TASK, "Task"),
        (ACTION_MEMBER, "Member"),
        (ACTION_GROUP, "Group"),
        (ACTION_PROJECT, "Project"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="activity_logs",
        null=True,
        blank=True,
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        related_name="activity_logs",
        null=True,
        blank=True,
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def icon_class(self):
        return {
            self.ACTION_COMMENT: "bi-chat-left-dots text-info",
            self.ACTION_TASK: "bi-list-check text-primary",
            self.ACTION_MEMBER: "bi-person-plus text-warning",
            self.ACTION_GROUP: "bi-people text-success",
            self.ACTION_PROJECT: "bi-folder2-open text-secondary",
        }.get(self.action_type, "bi-clock-history text-muted")
