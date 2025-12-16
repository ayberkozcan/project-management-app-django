from django import forms
from .models import Project, ProjectMember

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

class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ["user", "role"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"})
        }