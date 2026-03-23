from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView

from groups.models import Group
from projects.forms import ProjectForm, ProjectGroupForm, ProjectMemberForm, ProjectTaskForm
from tasks.models import Task
from .models import Project, ProjectMember
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages

@login_required
def dashboard(request):
    projects_count = Project.objects.filter(users=request.user).count()
    tasks_count = Task.objects.filter(assignees=request.user).count()
    created_not_assigned_tasks_count = Task.objects.filter(Q(owner=request.user) & ~Q(assignees=request.user)).count()
    groups_count = Group.objects.filter(group_members__user=request.user).count()
    return render(request, "projects/dashboard.html", 
        {
            "projects_count": projects_count,
            "assigned_tasks_count": tasks_count,
            "created_not_assigned_tasks_count": created_not_assigned_tasks_count,
            "groups_count": groups_count
        }
    )

@login_required
def profile(request):
    return render(request, "projects/profile.html")

def user_is_project_admin(project, user):
    return (
        project.owner == user or
        project.members.filter(user=user, role="admin").exists()
    )

def user_is_project_member(project, user):
    return (
        project.owner == user or
        project.members.filter(user=user).exists()
    )

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    login_url = "/accounts/login/"

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user) | Q(members__user=user)).distinct()

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/assigned_tasks_list.html"
    context_object_name = "tasks"
    login_url = "/accounts/login/"

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(Q(owner=user) | Q(assignees=user)).distinct()

class ProjectMembersView(LoginRequiredMixin, ListView):
    model = ProjectMember
    template_name = "projects/project_members.html"
    context_object_name = "project_members"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs["project_id"])

        is_owner = self.project.owner == request.user
        is_member = self.project.members.filter(user=request.user).exists()

        if not (is_owner or is_member):
            raise PermissionDenied
    
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.project.members.select_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project

        pm = ProjectMember.objects.filter(project=self.project, user=self.request.user).first()
        context["user_can_manage_project"] = (
            self.project.owner == self.request.user or
            (pm and pm.role == "admin")
        )

        return context
    
class ProjectGroupsView(LoginRequiredMixin, ListView):
    model = Project
    group_model = Group
    template_name = "projects/project_groups.html"
    context_object_name = "project_groups"
    login_url = "/accounts/login/"

    def get_project(self):
        project = get_object_or_404(Project, id=self.kwargs["project_id"])

        if not user_is_project_member(project, self.request.user):
            raise PermissionDenied

        return project
    
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
            response = super().form_valid(form)

            ProjectMember.objects.create(
                project=self.object,
                user=self.request.user,
                role="admin"
            )

            return response

        except IntegrityError:
            form.add_error("name", "A project with this name already exists.")
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

    if membership.user == project.owner:
        messages.error(request, "Project owner cannot be removed.")
        return redirect("project_members", project_id=project.id)

    membership.delete()
    messages.success(request, "Member removed successfully.")

    return redirect("project_members", project_id=project.id)

class ProjectTasksView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "projects/project_tasks.html"
    context_object_name = "project_tasks"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs["project_id"])

        if not user_is_project_member(self.project, request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Task.objects
            .filter(project=self.project)
            .select_related("assigned_group", "owner")
            .prefetch_related("assignees")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["can_manage_tasks"] = (
            self.project.owner == self.request.user or
            self.project.members.filter(
                user=self.request.user,
                role="admin"
            ).exists()
        )
        return context
    
class AddTaskView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = ProjectTaskForm
    template_name = "tasks/task_form.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs["project_id"])

        if not user_is_project_admin(self.project, request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.owner = self.request.user

        response = super().form_valid(form)

        if self.object.assigned_group:
            self.object.assignees.add(
                *self.object.assigned_group.members.all()
            )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def get_success_url(self):
        return reverse("project_tasks", kwargs={"project_id": self.project.id})
    
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = ProjectTaskForm
    template_name = "tasks/task_form.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not user_is_project_admin(self.object.project, request.user):
            raise PermissionDenied

        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context

    def get_success_url(self):
        return reverse(
            "project_tasks",
            kwargs={"project_id": self.object.project.id}
        )