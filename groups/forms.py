from django import forms
from .models import Group, GroupMember
from django.contrib.auth import get_user_model

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Group name"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Group description",
                "rows": 4
            }),
        }

User = get_user_model()

class GroupMemberForm(forms.ModelForm):
    class Meta:
        model = GroupMember
        fields = ["user", "role"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"})
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop("group")
        super().__init__(*args, **kwargs)

        existing_user = group.group_members.values_list("user_id", flat=True)

        self.fields["user"].queryset = User.objects.exclude(id__in=existing_user)