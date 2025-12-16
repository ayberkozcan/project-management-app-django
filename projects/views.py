from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from .models import Project, ProjectMember
from django.urls import reverse_lazy

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    login_url = "/accounts/login/"

class ProjectMembersListView(LoginRequiredMixin, ListView):
    model = ProjectMember
    template_name = "projects/project_members_list.html"
    context_object_name = "project_members"
    login_url = "/accounts/login/"

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = "projects/project_form.html"
    fields = ["name", "description"]
    success_url = reverse_lazy("project-list")

    login_url = "/accounts/login/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)