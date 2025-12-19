from django.urls import path
from .views import ProjectListView, ProjectMembersView, ProjectCreateView, AddMemberView, ProjectUpdateView, ProjectDeleteView, ProjectDetailView, remove_project_member

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list"),
    path("create/", ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("<int:pk>/delete/", ProjectDeleteView.as_view(), name="project_delete"),
    path("<int:project_id>/members/", ProjectMembersView.as_view(), name="project_members"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path("<int:project_id>/members/add/", AddMemberView.as_view(), name="member_add"),
    path("<int:project_id>/members/<int:member_id>/remove", remove_project_member, name="member_remove"),
]
