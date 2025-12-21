from django.urls import path
from .views import GroupListView, GroupCreateView

urlpatterns = [
    path("", GroupListView.as_view(), name="group_list"),
    path("create/", GroupCreateView.as_view(), name="group_create"),
]
