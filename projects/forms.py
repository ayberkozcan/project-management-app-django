from django import forms
from .models import Project, ProjectMember
from django.contrib.auth import get_user_model

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]
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