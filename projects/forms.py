from django import forms

from groups.models import Group
from tasks.models import Task
from .models import Comment, Project, ProjectMember
from django.contrib.auth import get_user_model
from django.db.models import Count

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "deadline"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Project name"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Project description",
                "rows": 4
            }),
            "deadline": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local"
            }),
        }

User = get_user_model()

class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ["user", "role"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"})
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project")
        super().__init__(*args, **kwargs)

        existing_user = project.members.values_list("user_id", flat=True)

        self.fields["user"].queryset = User.objects.exclude(id__in=existing_user)
        
class ProjectGroupForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project")
        super().__init__(*args, **kwargs)

        assigned_groups = project.assigned_groups.values_list("id", flat=True)

        self.fields["group"].queryset = Group.objects.filter(
            owner=project.owner
        ).exclude(id__in=assigned_groups)


MAX_ASSIGNEES = 5

class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["name", "description", "deadline", "assigned_group", "assignees"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Task name"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Task description",
                "rows": 4
            }),
            "deadline": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local"
            }),
            "assigned_group": forms.Select(attrs={
                "class": "form-control",
            }),
            "assignees": forms.SelectMultiple(attrs={
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if not self.project:
            return

        self.fields["assigned_group"].queryset = self.project.assigned_groups.all()
        self.fields["assigned_group"].required = False

        self.fields["assignees"].queryset = User.objects.filter(
            projectmember__project=self.project
        )
        self.fields["assignees"].required = False

    def clean_assignees(self):
        assignees = self.cleaned_data.get("assignees")
        if assignees and assignees.count() > MAX_ASSIGNEES:
            raise forms.ValidationError(f"You can assign at most {MAX_ASSIGNEES} users to this task.")
        return assignees


class ProjectCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["task", "content"]
        widgets = {
            "task": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "maxlength": Comment.MAX_CONTENT_LENGTH,
                    "placeholder": "Write a short project comment...",
                }
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)
        self.fields["task"].required = False
        self.fields["task"].empty_label = "General project comment"
        self.fields["task"].queryset = (
            project.tasks.order_by("name") if project else Task.objects.none()
        )

    def clean_task(self):
        task = self.cleaned_data.get("task")
        if task and self.project and task.project_id != self.project.id:
            raise forms.ValidationError("Selected task does not belong to this project.")
        return task


class GroupCommentForm(forms.ModelForm):
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Comment
        fields = ["project", "task", "content"]
        widgets = {
            "task": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "maxlength": Comment.MAX_CONTENT_LENGTH,
                    "placeholder": "Write a short group comment...",
                }
            ),
        }

    def __init__(self, *args, group=None, **kwargs):
        self.group = group
        super().__init__(*args, **kwargs)
        allowed_projects = group.projects.order_by("name") if group else Project.objects.none()
        self.fields["project"].queryset = allowed_projects
        self.fields["task"].required = False
        self.fields["task"].empty_label = "General group comment"
        self.fields["task"].queryset = Task.objects.filter(
            project__in=allowed_projects
        ).select_related("project").order_by("project__name", "name")

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        task = cleaned_data.get("task")

        if self.group and project and not self.group.projects.filter(id=project.id).exists():
            self.add_error("project", "Selected project is not assigned to this group.")

        if task and project and task.project_id != project.id:
            self.add_error("task", "Selected task does not belong to the chosen project.")

        return cleaned_data
