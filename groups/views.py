from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied

from .models import Group

from groups.forms import GroupForm

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "groups/group_list.html"
    context_object_name = "groups"
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Group.objects.filter(members=self.request.user)
    
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

    def get_group(self):
        group = get_object_or_404(Group, id=self.kwargs["group_id"])

        if (
            group.owner == self.request.user or
            group.members.filter(user=self.request.user).exists()
        ):
            return group
        
        raise PermissionDenied
    
    def get_queryset(self):
        return self.get_group().members.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.get_group()
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

        group.members.add(self.request.user)

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
    