from django.urls import path
from .views import *

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list"),
    path("create/", ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("<int:pk>/delete/", ProjectDeleteView.as_view(), name="project_delete"),

    path("<int:project_id>/members/", ProjectMembersView.as_view(), name="project_members"),
    path("<int:project_id>/members/add/", AddMemberView.as_view(), name="member_add"),
    path("<int:project_id>/members/<int:member_id>/remove", remove_project_member, name="member_remove"),
    
    path("<int:project_id>/groups/", ProjectGroupsView.as_view(), name="project_groups"),
    path("<int:project_id>/groups/add/", AddGroupView.as_view(), name="group_add"),

    path("tasks/", TaskListView.as_view(), name="assigned_tasks_list"),
    path("<int:project_id>/tasks/", ProjectTasksView.as_view(), name="project_tasks"),
    path("<int:project_id>/tasks/add/", AddTaskView.as_view(), name="task_add"),
    path("tasks/<int:pk>/edit/", TaskUpdateView.as_view(), name="task_edit"),
    
    path("<int:project_id>/comments/", ProjectCommentListView.as_view(), name="project_comments"),
    path("<int:project_id>/comments/<int:comment_id>/delete/", delete_project_comment, name="project_comment_delete"),
    path("<int:project_id>/activitylogs/", ProjectMembersView.as_view(), name="project_activity"),
]
