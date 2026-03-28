from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from .forms import AccountSignupForm, AccountLoginForm
from config.rate_limits import RateLimitMixin

class AccountLoginView(RateLimitMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = AccountLoginForm
    rate_limit = "5/m"
    rate_limit_scope = "login"
    rate_limit_key = "ip"
    rate_limit_methods = {"POST"}
    
    def get_success_url(self):
        return reverse_lazy("dashboard")

class SignUpView(RateLimitMixin, CreateView):
    form_class = AccountSignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")
    rate_limit = "3/m"
    rate_limit_scope = "signup"
    rate_limit_key = "ip"
    rate_limit_methods = {"POST"}
