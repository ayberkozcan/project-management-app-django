from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from .forms import AccountSignupForm, AccountLoginForm

class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AccountLoginForm
    
    def get_success_url(self):
        return reverse_lazy("dashboard")

class SignUpView(CreateView):
    form_class = AccountSignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")