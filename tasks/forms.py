from django import forms
from django.contrib.auth import get_user_model

from .models import Task
from groups.models import Group

User = get_user_model()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["name", "description", "deadline"]
        widgets = {
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            )
        }

class AssignGroupForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        empty_label="Select a group"
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = Group.objects.filter(
            project=project
        )

class AssignIndividualForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        empty_label="Select a user"
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["user"].queryset = User.objects.filter(
            custom_groups__project=project
        ).distinct()