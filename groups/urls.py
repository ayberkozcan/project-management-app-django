from django.urls import path
from .views import GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView, GroupProjectsView, GroupMembersView

urlpatterns = [
    path("", GroupListView.as_view(), name="group_list"),
    path("create/", GroupCreateView.as_view(), name="group_create"),
    path("<int:group_id>/edit/", GroupUpdateView.as_view(), name="group_edit"),
    path("<int:pk>/delete/", GroupDeleteView.as_view(), name="group_delete"),
    path("<int:group_id>/projects/", GroupProjectsView.as_view(), name="group_projects"),
    path("<int:group_id>/members/", GroupMembersView.as_view(), name="group_members")
]
