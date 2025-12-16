from django.urls import path
from .views import ProjectListView, ProjectMembersView, ProjectCreateView, AddMemberView, ProjectUpdateView

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list"),
    path("create/", ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("<int:project_id>/members/", ProjectMembersView.as_view(), name="project_members"),
    path("<int:project_id>/members/add/", AddMemberView.as_view(), name="member_add"),
]
