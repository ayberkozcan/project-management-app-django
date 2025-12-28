from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView

from groups.forms import GroupMemberForm
from groups.models import Group, GroupMember
from projects.forms import ProjectForm, ProjectGroupForm, ProjectMemberForm
from .models import Project, ProjectMember
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

@login_required
def dashboard(request):
    projects_count = Project.objects.filter(owner=request.user).count()
    return render(request, "projects/dashboard.html", {"projects_count": projects_count})

@login_required
def profile(request):
    return render(request, "projects/profile.html")

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    login_url = "/accounts/login/"

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user) | Q(assigned_groups__members=user)).distinct()

class ProjectMembersView(LoginRequiredMixin, ListView):
    model = ProjectMember
    template_name = "projects/project_members.html"
    context_object_name = "project_members"
    login_url = "/accounts/login/"

    def get_project(self):
        project = get_object_or_404(Project, id=self.kwargs["project_id"])

        if (
            project.owner == self.request.user or
            project.members.filter(user=self.request.user).exists()
        ):
            return project
    
        raise PermissionDenied

    def get_queryset(self):
        project = self.get_project()
        return ProjectMember.objects.filter(project=project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
    
class ProjectGroupsView(LoginRequiredMixin, ListView):
    model = Project
    group_model = Group
    template_name = "projects/project_groups.html"
    context_object_name = "project_groups"
    login_url = "/accounts/login/"

    def get_project(self):
        project = get_object_or_404(Project, id=self.kwargs["project_id"])

        is_owner = project.owner == self.request.user
        is_admin = project.members.filter(user=self.request.user, role="admin").exists()
        is_member = project.members.filter(user=self.request.user).exists()

        if is_owner or is_admin or is_member:
            return project
        
        raise PermissionDenied
    
    def get_queryset(self):
        project = self.get_project()
        return Group.objects.filter(projects=project)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    
    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse("project_list")

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return (
            Project.objects.filter(owner=self.request.user) |
            Project.objects.filter(members__user=self.request.user)
        ).distinct()

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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        try:
            return super().form_valid(form)
        except IntegrityError:
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
    
class AddGroupView(LoginRequiredMixin, FormView):
    form_class = ProjectGroupForm
    template_name = "projects/group_form.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project,
            id=kwargs["project_id"]
        )

        if not (
            self.project.owner == request.user or
            ProjectMember.objects.filter(
                project=self.project,
                user=request.user,
                role="admin"
            ).exists()
        ):
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def form_valid(self, form):
        group = form.cleaned_data["group"]

        if group in self.project.assigned_groups.all():
            form.add_error("group", "This group is already assigned to this project.")
            return self.form_invalid(form)

        self.project.assigned_groups.add(group)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context
    
    def get_success_url(self):
        return reverse_lazy("project_groups", kwargs={"project_id": self.project.id})

@login_required
def remove_project_member(request, project_id, member_id):
    if request.method != "POST":
        raise PermissionDenied
    
    project = get_object_or_404(Project, id=project_id)

    if project.owner != request.user:
        raise PermissionDenied
    
    membership = get_object_or_404(
        ProjectMember,
        project=project,
        user_id=member_id
    )
    membership.delete()

    return redirect("project_members", project_id=project.id)