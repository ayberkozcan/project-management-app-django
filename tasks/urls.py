from django.urls import path
from .views import *

urlpatterns = [
    path("projects/<int:project_id>/tasks/create/", TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:task_id>/edit/", TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:task_id>/assign-group/", assign_group_to_task, name="assign_group"),
    path("tasks/<int:task_id>/assign-individual/", assign_individual_to_task, name="assign_individual"),
]
