from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import AccountSignupForm

class SignUpView(CreateView):
    form_class = AccountSignupForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")