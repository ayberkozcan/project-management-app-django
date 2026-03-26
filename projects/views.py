from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView

from groups.models import Group
from accounts.forms import ProfileEditForm
from projects.activity import log_activity
from projects.forms import GroupCommentForm, ProjectCommentForm, ProjectForm, ProjectGroupForm, ProjectMemberForm, ProjectTaskForm
from tasks.models import Task
from .models import ActivityLog, Comment, Project, ProjectMember
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST

@login_required
def dashboard(request):
    projects_count = Project.objects.filter(users=request.user).count()
    tasks_count = Task.objects.filter(assignees=request.user).count()
    created_not_assigned_tasks_count = Task.objects.filter(Q(owner=request.user) & ~Q(assignees=request.user)).count()
    groups_count = Group.objects.filter(group_members__user=request.user).count()
    activities = (
        ActivityLog.objects.filter(actor=request.user)
        .select_related("project", "group", "task")
        .order_by("-created_at")[:3]
    )
    return render(request, "projects/dashboard.html", 
        {
            "projects_count": projects_count,
            "assigned_tasks_count": tasks_count,
            "created_not_assigned_tasks_count": created_not_assigned_tasks_count,
            "groups_count": groups_count,
            "activities": activities,
        }
    )

@login_required
def profile(request):
    projects_count = Project.objects.filter(users=request.user).count()
    tasks_count = Task.objects.filter(assignees=request.user).count()
    created_not_assigned_tasks_count = Task.objects.filter(Q(owner=request.user) & ~Q(assignees=request.user)).count()
    groups_count = Group.objects.filter(group_members__user=request.user).count()
    activities = (
        ActivityLog.objects.filter(actor=request.user)
        .select_related("project", "group", "task")
        .order_by("-created_at")[:5]
    )
    return render(request, "projects/profile.html", 
        {
            "projects_count": projects_count,
            "assigned_tasks_count": tasks_count,
            "created_not_assigned_tasks_count": created_not_assigned_tasks_count,
            "groups_count": groups_count,
            "activities": activities,
        }
    )


class AllActivityView(LoginRequiredMixin, ListView):
    model = ActivityLog
    template_name = "projects/activity_list.html"
    context_object_name = "activities"
    login_url = "/accounts/login/"
    paginate_by = 8

    def get_queryset(self):
        return (
            ActivityLog.objects.filter(actor=self.request.user)
            .select_related("project", "group", "task")
            .order_by("-created_at")
        )


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "projects/profile_form.html", {"form": form})

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


def user_can_manage_project_comments(project, user):
    return (
        project.owner == user or
        project.members.filter(user=user, role="admin").exists()
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
            log_activity(
                actor=self.request.user,
                project=self.object,
                action_type=ActivityLog.ACTION_PROJECT,
                description=f"created the project {self.object.name}",
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
        return reverse("project_detail", kwargs={"pk": self.object.id})

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            actor=self.request.user,
            project=self.object,
            action_type=ActivityLog.ACTION_PROJECT,
            description=f"updated the project {self.object.name}",
        )
        return response

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = kwargs.get("comment_form") or ProjectCommentForm(
            project=self.object
        )
        all_comments = self.object.comments.select_related(
            "author",
            "task",
        )
        context["comments"] = all_comments[:3]
        context["recent_activities"] = self.object.activity_logs.select_related(
            "actor",
            "task",
            "group",
        )[:3]
        context["total_comment_count"] = all_comments.count()
        context["remaining_comment_count"] = max(context["total_comment_count"] - 3, 0)
        context["can_manage_comments"] = user_can_manage_project_comments(
            self.object,
            self.request.user,
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProjectCommentForm(request.POST, project=self.object)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.project = self.object
            comment.save()
            log_activity(
                actor=request.user,
                project=self.object,
                action_type=ActivityLog.ACTION_COMMENT,
                description=(
                    f"commented on {comment.task.name}"
                    if comment.task
                    else "added a project comment"
                ),
                task=comment.task,
            )
            messages.success(request, "Comment added successfully.")
            return redirect("project_detail", pk=self.object.id)

        context = self.get_context_data(comment_form=form)
        return self.render_to_response(context)


class ProjectCommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = "projects/project_comments.html"
    context_object_name = "comments"
    login_url = "/accounts/login/"
    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs["project_id"])

        if not user_is_project_member(self.project, request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.project.comments.select_related("author", "task")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["can_manage_comments"] = user_can_manage_project_comments(
            self.project,
            self.request.user,
        )
        return context


@login_required
@require_POST
def delete_project_comment(request, project_id, comment_id):
    project = get_object_or_404(Project, id=project_id)

    if not user_can_manage_project_comments(project, request.user):
        raise PermissionDenied

    comment = get_object_or_404(Comment, id=comment_id, project=project)
    task = comment.task
    comment.delete()
    log_activity(
        actor=request.user,
        project=project,
        action_type=ActivityLog.ACTION_COMMENT,
        description=(
            f"deleted a comment on {task.name}"
            if task
            else "deleted a project comment"
        ),
        task=task,
    )
    messages.success(request, "Comment deleted successfully.")

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("project_comments", project_id=project.id)

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
            response = super().form_valid(form)
            log_activity(
                actor=self.request.user,
                project=self.project,
                action_type=ActivityLog.ACTION_MEMBER,
                description=f"added {self.object.user.username} to the project",
            )
            return response
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
        log_activity(
            actor=self.request.user,
            project=self.project,
            group=group,
            action_type=ActivityLog.ACTION_GROUP,
            description=f"assigned group {group.name} to the project",
        )
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
    log_activity(
        actor=request.user,
        project=project,
        action_type=ActivityLog.ACTION_MEMBER,
        description=f"removed {membership.user.username} from the project",
    )
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

        description = f"created task {self.object.name}"
        if self.object.assigned_group:
            description += f" and assigned group {self.object.assigned_group.name}"
        log_activity(
            actor=self.request.user,
            project=self.project,
            group=self.object.assigned_group,
            task=self.object,
            action_type=ActivityLog.ACTION_TASK,
            description=description,
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

    def form_valid(self, form):
        response = super().form_valid(form)
        description = f"updated task {self.object.name}"
        if self.object.assigned_group:
            description += f" for group {self.object.assigned_group.name}"
        log_activity(
            actor=self.request.user,
            project=self.object.project,
            group=self.object.assigned_group,
            task=self.object,
            action_type=ActivityLog.ACTION_TASK,
            description=description,
        )
        return response

    def get_success_url(self):
        return reverse(
            "project_tasks",
            kwargs={"project_id": self.object.project.id}
        )
