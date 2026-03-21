from django.urls import path
from .views import *

app_name = "tasks"

urlpatterns = [
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("projects/<int:project_id>/tasks/create/", TaskCreateView.as_view(), name="task_create"),
    path("<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("tasks/<int:task_id>/edit/", TaskEditView.as_view(), name="task_edit"),
    path("tasks/<int:task_id>/assign-group/", assign_group_to_task, name="assign_group"),
    path("tasks/<int:task_id>/assign-individual/", assign_individual_to_task, name="assign_individual"),
]
