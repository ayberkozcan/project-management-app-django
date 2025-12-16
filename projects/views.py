from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView

from projects.forms import ProjectForm, ProjectMemberForm
from .models import Project, ProjectMember
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    login_url = "/accounts/login/"

class ProjectMembersView(LoginRequiredMixin, ListView):
    model = ProjectMember
    template_name = "projects/project_members.html"
    context_object_name = "project_members"
    login_url = "/accounts/login/"

    def get_queryset(self):
        project = get_object_or_404(
            Project,
            id=self.kwargs["project_id"],
            owner=self.request.user
        )
        return ProjectMember.objects.filter(project=project).select_related("user")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(
            Project,
            id=self.kwargs["project_id"],
            owner=self.request.user
        )
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("project_list")
    login_url = "/accounts/login/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        try:
            return super().form_valid(form)
        except:
            form.add_error(
                "name",
                "A project with this name already exists."
            )
            return self.form_invalid(form)
    
class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    login_url = "/accounts/login/"

    def get_success_url(self):
        return reverse("project_list")

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

class AddMemberView(LoginRequiredMixin, CreateView):
    model = ProjectMember
    form_class = ProjectMemberForm
    template_name = "projects/member_form.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project,
            id=kwargs["project_id"],
            owner=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.project = self.project
        try:
            return super().form_valid(form)
        except:
            form.add_error(
                "user",
                "This user is already a member of this project."
            )
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context
    
    def get_success_url(self):
        return reverse_lazy("project_members", kwargs={"project_id": self.project.id})