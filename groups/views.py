from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from .models import Group

from groups.forms import GroupForm

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "groups/group_list.html"
    context_object_name = "groups"
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Group.objects.filter(members=self.request.user)
    
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