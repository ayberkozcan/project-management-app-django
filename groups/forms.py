from django import forms
from .models import Group

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