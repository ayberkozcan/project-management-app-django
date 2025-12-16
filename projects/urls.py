from django.urls import path
from .views import ProjectListView, ProjectMembersListView, ProjectCreateView

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list"),
    path("create/", ProjectCreateView.as_view(), name="project-create"),
    path("members/", ProjectMembersListView.as_view(), name="project_members_list"),
]
