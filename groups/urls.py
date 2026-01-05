from django.urls import path
from .views import *

urlpatterns = [
    path("", GroupListView.as_view(), name="group_list"),
    path("create/", GroupCreateView.as_view(), name="group_create"),
    path("my-invites/", MyGroupInvitesView.as_view(), name="my_group_invites"),
    path("<int:pk>/edit/", GroupUpdateView.as_view(), name="group_edit"),
    path("<int:pk>/delete/", GroupDeleteView.as_view(), name="group_delete"),
    path("<int:pk>/detail/", GroupDetailView.as_view(), name="group_detail"),
    path("<int:group_id>/projects/", GroupProjectsView.as_view(), name="group_projects"),
    path("<int:group_id>/members/", GroupMembersView.as_view(), name="group_members"),
    path("<int:group_id>/member/add/", SendGroupInviteView.as_view(), name="group_member_add"),
    path("<int:group_id>/members/<int:member_id>/remove", remove_group_member, name="group_member_remove"),
    path("<int:invite_id>/accept/", accept_group_invite, name="accept_group_invite"),
    path("<int:invite_id>/refuse/", refuse_group_invite, name="refuse_group_invite"),
]
