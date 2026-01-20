from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView

from groups.forms import GroupMemberForm
from groups.models import Group, GroupMember, User
from projects.forms import ProjectForm, ProjectGroupForm, ProjectMemberForm
from tasks.forms import AssignGroupForm, AssignIndividualForm, TaskForm
from .models import Project, ProjectMember, Task
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST

def is_project_admin(user, project):
    if project.owner == user:
        return True
    
    return Group.objects.filter(
        project=project,
        owner=user
    ).exists()

def check_project_admin(user, project):
    if not is_project_admin(user, project):
        raise PermissionDenied("You do not have permission to perform this action.")

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=self.kwargs["project_id"])

        if not is_project_admin(request.user, self.project):
            raise PermissionDenied("You are not allowed to create tasks for this project.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.project = self.project
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context
    
    def get_success_url(self):
        return reverse("project_detail", args=[self.project.id])
    
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not is_project_admin(request.user, self.object.project):
            raise PermissionDenied("You are not allowed to edit this task.")
    
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context
    
    def get_success_url(self):
        return reverse("project_detail", args=[self.object.project.id])

@login_required
@require_POST
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

    messages.success(request, "The task has been successfully assigned to the group.")
    return redirect("task_detail", task.id)

@login_required
@require_POST
def assign_individual_to_task(request, task_id):
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

    task.assignees.clear()
    task.assigned_group = None
    task.save(update_fields=["assigned_group"])

    task.assignees.add(user)

    messages.success(request, "The task has been successfully assigned to the user.")
    return redirect("task_detail", task.id)