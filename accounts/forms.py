import random
from django import forms
from django.utils.text import slugify
from django.contrib.auth.forms import UserCreationForm
from .models import Account

class AccountSignupForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)

        base_username = slugify(
            f"{self.cleaned_data['first_name']}_{self.cleaned_data['last_name']}"
        )

        username = base_username
        while Account.objects.filter(username=username).exists():
            username = f"{base_username}{random.randint(10, 99)}"

        user.username = username
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user