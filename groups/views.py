from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .models import Group, GroupMember

from groups.forms import GroupForm, GroupMemberForm

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

class GroupProjectsView(LoginRequiredMixin, ListView):
    template_name = "groups/group_projects.html"
    context_object_name = "group_projects"
    login_url = "/account/login"

    def get_group(self):
        group = get_object_or_404(Group, id=self.kwargs["group_id"])

        if (
            group.owner == self.request.user or
            group.members.filter(user=self.request.user).exists()
        ):
            return group
        
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

        return super().form_valid(form)

class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "groups/group_form.html"
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Group.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse("group_list")
    
class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = Group

    def get_queryset(self):
        return Group.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse("group_list")
    
class AddGroupMemberView(LoginRequiredMixin, CreateView):
    model = GroupMember
    form_class = GroupMemberForm
    template_name = "groups/group_member_form.html"
    login_url = "/accounts/login"

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(
            Group,
            id=kwargs["group_id"]
        )

        if self.group.owner == request.user:
            return super().dispatch(request, *args, **kwargs)
        
        membership = GroupMember.objects.filter(
            group=self.group, user=request.user
        ).first()

        if membership and membership.role == "admin":
            return super().dispatch(request, *args, **kwargs)

        return HttpResponseForbidden("You are not allowed to add members to this group.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["group"] = self.group
        return kwargs
    
    def form_valid(self, form):
        form.instance.group = self.group
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(
                "user",
                "This user is already a member of this group."
            )
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context
    
    def get_success_url(self):
        return reverse_lazy("group_members", kwargs={"group_id": self.group.id})