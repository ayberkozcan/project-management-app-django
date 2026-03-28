from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView

from groups.forms import GroupMemberForm
from groups.models import Group, GroupMember, User
from projects.forms import ProjectForm, ProjectGroupForm, ProjectMemberForm
from tasks.forms import AssignGroupForm, AssignIndividualForm, TaskForm
from .models import Project, Task
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST
from projects.activity import log_activity
from projects.models import ActivityLog, ProjectMember
from config.rate_limits import RateLimitMixin, rate_limit

def is_project_admin(user, project):
    if project.owner == user:
        return True
    
    return ProjectMember.objects.filter(
        project=project,
        user=user,
        role="admin",
    ).exists()

def check_project_admin(user, project):
    if not is_project_admin(user, project):
        raise PermissionDenied("You do not have permission to perform this action.")

class TaskListView(LoginRequiredMixin, RateLimitMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    login_url = "/accounts/login/"
    rate_limit = "60/m"
    rate_limit_scope = "task-list"
    rate_limit_methods = {"GET"}

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(Q(owner=user) | Q(assignees=user)).distinct()

class TaskCreateView(LoginRequiredMixin, RateLimitMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    login_url = "/accounts/login/"
    rate_limit = "30/h"
    rate_limit_scope = "task-create"
    rate_limit_methods = {"POST"}

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=self.kwargs["project_id"])

        if not is_project_admin(request.user, self.project):
            raise PermissionDenied("You are not allowed to create tasks for this project.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.project = self.project
        response = super().form_valid(form)
        log_activity(
            actor=self.request.user,
            project=self.project,
            task=self.object,
            action_type=ActivityLog.ACTION_TASK,
            description=f"created task {self.object.name}",
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context
    
    def get_success_url(self):
        return reverse("project_detail", args=[self.project.id])
    
class TaskEditView(LoginRequiredMixin, RateLimitMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    login_url = "/accounts/login/"
    rate_limit = "60/h"
    rate_limit_scope = "task-edit"
    rate_limit_methods = {"POST"}

    pk_url_kwarg = "task_id"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not is_project_admin(request.user, self.object.project):
            raise PermissionDenied("You are not allowed to edit this task.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = self.object
        return context

    def get_success_url(self):
        return reverse("tasks:task_detail", args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            actor=self.request.user,
            project=self.object.project,
            task=self.object,
            action_type=ActivityLog.ACTION_TASK,
            description=f"updated task {self.object.name}",
        )
        return response

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    
    def get_queryset(self):
        return Task.objects.filter(
            Q(project__owner=self.request.user) |
            Q(project__members__user=self.request.user, project__members__role="admin")
        ).distinct()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        project = self.object.project
        task_name = self.object.name
        response = super().delete(request, *args, **kwargs)
        log_activity(
            actor=request.user,
            project=project,
            action_type=ActivityLog.ACTION_TASK,
            description=f"deleted task {task_name}",
        )
        return response

    def get_success_url(self):
        return reverse("project_detail", args=[self.object.project_id])

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return (
            Task.objects.filter(project__owner=self.request.user) |
            Task.objects.filter(project__members__user=self.request.user) |
            Task.objects.filter(assignees=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_task"] = is_project_admin(
            self.request.user,
            self.object.project,
        )
        return context

@login_required
@require_POST
@rate_limit(scope="task-assign-group", rate="30/h", methods={"POST"})
def assign_group_to_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project = task.project

    check_project_admin(request.user, project)

    form = AssignGroupForm(request.POST, project=project)
    if not form.is_valid():
        return render(
            request,
            "tasks/assign_members.html",
            {
                "form": form,
                "task": task,
                "project": project,
                "assign_type": "group",
            }
        )

    group = form.cleaned_data["group"]

    task.assignees.clear()
    task.assigned_group = group
    task.save(update_fields=["assigned_group"])

    task.assignees.add(*group.members.all())
    log_activity(
        actor=request.user,
        project=project,
        group=group,
        task=task,
        action_type=ActivityLog.ACTION_TASK,
        description=f"assigned group {group.name} to task {task.name}",
    )

    messages.success(request, "The task has been successfully assigned to the group.")
    return redirect("task_detail", task.id)

@login_required
@require_POST
@rate_limit(scope="task-assign-individual", rate="30/h", methods={"POST"})
def assign_individual_to_task(request, task_id):
    MAX_ASSIGNEES = 5

    task = get_object_or_404(Task, id=task_id)
    project = task.project

    check_project_admin(request.user, project)

    form = AssignIndividualForm(request.POST, project=project)
    if not form.is_valid():
        return render(
            request,
            "tasks/assign_members.html",
            {
                "form": form,
                "task": task,
                "project": project,
                "assign_type": "individual",
            }
        )

    user = form.cleaned_data["user"]

    if task.assignees.count() >= MAX_ASSIGNEES:
        messages.error(request, f"This task already has the maximum of {MAX_ASSIGNEES} assignees.")
        return redirect("tasks:task_detail", task.id)

    task.assignees.clear()
    task.assigned_group = None
    task.save(update_fields=["assigned_group"])

    task.assignees.add(user)
    log_activity(
        actor=request.user,
        project=project,
        task=task,
        action_type=ActivityLog.ACTION_TASK,
        description=f"assigned {user.username} to task {task.name}",
    )

    messages.success(request, "The task has been successfully assigned to the user.")
    return redirect("tasks:task_detail", task.id)
