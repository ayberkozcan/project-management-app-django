import random
from django import forms
from django.utils.text import slugify
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Account

class AccountLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Email Address"
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password"
        })
    )

class AccountSignupForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ("first_name", "last_name", "email")

    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "First Name",
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Last Name",
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Email Address",
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm Password",
        })
    )

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