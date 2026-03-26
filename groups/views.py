from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.views.decorators.http import require_POST

from projects.forms import GroupCommentForm, User
from projects.activity import log_activity
from projects.models import ActivityLog, Comment

from .models import Group, GroupInvite, GroupMember

from groups.forms import GroupForm, GroupInviteForm, GroupMemberForm

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "groups/group_list.html"
    context_object_name = "groups"
    login_url = "/accounts/login/"

    def get_queryset(self):
        user = self.request.user
        return Group.objects.filter(
            Q(owner=user) | Q(group_members__user=user)
        ).distinct()


def user_can_manage_group_comments(group, user):
    return (
        group.owner == user or
        group.group_members.filter(user=user, role="admin").exists()
    )
    
class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = "groups/group_detail.html"
    login_url = "/accounts/login/"
    context_object_name = "group"

    def get_queryset(self):
        return (
            Group.objects.filter(owner=self.request.user) |
            Group.objects.filter(group_members__user=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = kwargs.get("comment_form") or GroupCommentForm(
            group=self.object
        )
        all_comments = self.object.comments.select_related(
            "author",
            "project",
            "task",
        )
        context["comments"] = all_comments[:3]
        context["recent_activities"] = self.object.activity_logs.select_related(
            "actor",
            "project",
            "task",
        )[:3]
        context["total_comment_count"] = all_comments.count()
        context["remaining_comment_count"] = max(context["total_comment_count"] - 3, 0)
        context["can_manage_comments"] = user_can_manage_group_comments(
            self.object,
            self.request.user,
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = GroupCommentForm(request.POST, group=self.object)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.group = self.object
            comment.save()
            log_activity(
                actor=request.user,
                project=comment.project,
                group=self.object,
                action_type=ActivityLog.ACTION_COMMENT,
                description=(
                    f"commented on {comment.task.name}"
                    if comment.task
                    else f"added a group comment in {comment.project.name}"
                ),
                task=comment.task,
            )
            messages.success(request, "Comment added successfully.")
            return redirect("group_detail", pk=self.object.id)

        context = self.get_context_data(comment_form=form)
        return self.render_to_response(context)


class GroupCommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = "groups/group_comments.html"
    context_object_name = "comments"
    login_url = "/accounts/login/"
    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, id=kwargs["group_id"])

        if not (
            self.group.owner == request.user or
            self.group.group_members.filter(user=request.user).exists()
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.group.comments.select_related("author", "project", "task")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        context["can_manage_comments"] = user_can_manage_group_comments(
            self.group,
            self.request.user,
        )
        return context


@login_required
@require_POST
def delete_group_comment(request, group_id, comment_id):
    group = get_object_or_404(Group, id=group_id)

    if not user_can_manage_group_comments(group, request.user):
        raise PermissionDenied

    comment = get_object_or_404(Comment, id=comment_id, group=group)
    project = comment.project
    task = comment.task
    comment.delete()
    log_activity(
        actor=request.user,
        project=project,
        group=group,
        action_type=ActivityLog.ACTION_COMMENT,
        description=(
            f"deleted a comment on {task.name}"
            if task
            else f"deleted a group comment in {project.name}"
        ),
        task=task,
    )
    messages.success(request, "Comment deleted successfully.")

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("group_comments", group_id=group.id)

class GroupProjectsView(LoginRequiredMixin, ListView):
    template_name = "groups/group_projects.html"
    context_object_name = "group_projects"
    login_url = "/accounts/login"

    def get_group(self):
        group = get_object_or_404(Group, id=self.kwargs["group_id"])

        if (
            group.owner == self.request.user or
            group.group_members.filter(user=self.request.user).exists()
        ):
            return group
        
        raise Http404("You are not allowed to access this group.")
        
    def get_queryset(self):
        return self.get_group().projects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.get_group()
        return context

class GroupMembersView(LoginRequiredMixin, ListView):
    template_name = "groups/group_members.html"
    context_object_name = "group_members"
    login_url = "/accounts/login"

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, id=kwargs["group_id"])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return self.group.group_members.select_related("user")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        
        gm = GroupMember.objects.filter(group=self.group, user=self.request.user).first()
        context["user_can_manage_group"] = (
            self.group.owner == self.request.user or
            (gm and gm.role == "admin")
        )
        
        return context
    
class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "groups/group_form.html"
    success_url = reverse_lazy("group_list")
    login_url = "/accounts/login/"

    def form_valid(self, form):
        group = form.save(commit=False)
        group.owner = self.request.user
        group.save()

        GroupMember.objects.create(
            group=group, user=self.request.user, role="admin"
        )
        if group.projects.exists():
            for project in group.projects.all():
                log_activity(
                    actor=self.request.user,
                    project=project,
                    group=group,
                    action_type=ActivityLog.ACTION_GROUP,
                    description=f"created group {group.name}",
                )

        return super().form_valid(form)

class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "groups/group_form.html"
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Group.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse("group_detail", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        response = super().form_valid(form)
        for project in self.object.projects.all():
            log_activity(
                actor=self.request.user,
                project=project,
                group=self.object,
                action_type=ActivityLog.ACTION_GROUP,
                description=f"updated group {self.object.name}",
            )
        return response
    
class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = Group

    def get_queryset(self):
        return Group.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse("group_list")

class SendGroupInviteView(LoginRequiredMixin, FormView):
    form_class = GroupInviteForm
    template_name = "groups/group_member_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, id=kwargs["group_id"])

        if not (
            self.group.owner == request.user or
            GroupMember.objects.filter(
                group=self.group,
                user=request.user,
                role="admin"
            ).exists()
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context

    def form_valid(self, form):
        identifier = form.cleaned_data["identifier"]

        user = User.objects.filter(
            Q(username__iexact=identifier) |
            Q(email__iexact=identifier)
        ).first()

        if not user:
            form.add_error("identifier", "User not found.")
            return self.form_invalid(form)

        if GroupMember.objects.filter(group=self.group, user=user).exists():
            form.add_error("identifier", "User is already a member.")
            return self.form_invalid(form)

        if GroupInvite.objects.filter(
            group=self.group,
            invited_user=user,
            accepted__isnull=True
        ).exists():
            form.add_error("identifier", "Invite already sent.")
            return self.form_invalid(form)

        GroupInvite.objects.create(
            group=self.group,
            invited_user=user,
            invited_by=self.request.user
        )

        for project in self.group.projects.all():
            log_activity(
                actor=self.request.user,
                project=project,
                group=self.group,
                action_type=ActivityLog.ACTION_MEMBER,
                description=f"invited {user.username} to the group",
            )

        return redirect("group_members", group_id=self.group.id)

class MyGroupInvitesView(LoginRequiredMixin, ListView):
    model = GroupInvite
    template_name = "groups/my_invites.html"
    context_object_name = "invites"

    def get_queryset(self):
        return GroupInvite.objects.filter(
            invited_user=self.request.user,
            accepted__isnull=True
        ).select_related("group", "invited_by")

@require_POST
@login_required
def accept_group_invite(request, invite_id):
    invite = get_object_or_404(
        GroupInvite,
        id=invite_id,
        invited_user=request.user,
        accepted__isnull=True
    )

    try:
        GroupMember.objects.get_or_create(
            group=invite.group,
            user=request.user,
            defaults={"role": "employee"}
        )
    except IntegrityError:
        pass

    invite.accepted = True
    invite.save(update_fields=["accepted"])

    for project in invite.group.projects.all():
        log_activity(
            actor=request.user,
            project=project,
            group=invite.group,
            action_type=ActivityLog.ACTION_MEMBER,
            description=f"joined the group {invite.group.name}",
        )

    return redirect("my_group_invites")

@require_POST
@login_required
def refuse_group_invite(request, invite_id):
    invite = get_object_or_404(
        GroupInvite,
        id=invite_id,
        invited_user=request.user,
        accepted__isnull=True
    )

    invite.delete()

    return redirect("my_group_invites")

# class AddGroupMemberView(LoginRequiredMixin, CreateView):
#     model = GroupMember
#     form_class = GroupMemberForm
#     template_name = "groups/group_member_form.html"
#     login_url = "/accounts/login"

#     def dispatch(self, request, *args, **kwargs):
#         self.group = get_object_or_404(
#             Group,
#             id=kwargs["group_id"]
#         )

#         if self.group.owner == request.user:
#             return super().dispatch(request, *args, **kwargs)
        
#         membership = GroupMember.objects.filter(
#             group=self.group, user=request.user
#         ).first()

#         if membership and membership.role == "admin":
#             return super().dispatch(request, *args, **kwargs)

#         return HttpResponseForbidden("You are not allowed to add members to this group.")
    
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["group"] = self.group
#         return kwargs
    
#     def form_valid(self, form):
#         form.instance.group = self.group
#         try:
#             return super().form_valid(form)
#         except IntegrityError:
#             form.add_error(
#                 "user",
#                 "This user is already a member of this group."
#             )
#             return self.form_invalid(form)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["group"] = self.group
#         return context
    
#     def get_success_url(self):
#         return reverse_lazy("group_members", kwargs={"group_id": self.group.id})
    
@login_required
def remove_group_member(request, group_id, member_id):
    if request.method != "POST":
        raise PermissionDenied
    
    group = get_object_or_404(Group, id=group_id)

    if group.owner != request.user:
        raise PermissionDenied
    
    membership = get_object_or_404(
        GroupMember,
        group=group,
        user_id=member_id
    )
    membership.delete()

    for project in group.projects.all():
        log_activity(
            actor=request.user,
            project=project,
            group=group,
            action_type=ActivityLog.ACTION_MEMBER,
            description=f"removed {membership.user.username} from the group",
        )

    GroupInvite.objects.filter(
        group=group,
        invited_user_id=member_id
    ).delete()

    return redirect("group_members", group_id=group.id)
