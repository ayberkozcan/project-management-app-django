from django.test import TestCase

from accounts.models import Account
from groups.models import Group, GroupMember
from projects.models import Project, ProjectMember
from tasks.models import Task


class GroupMembershipSyncTests(TestCase):
    def setUp(self):
        self.owner = Account.objects.create_user(
            email="owner@example.com",
            username="owner",
            password="testpass123",
            first_name="Owner",
            last_name="User",
        )
        self.member = Account.objects.create_user(
            email="member@example.com",
            username="member",
            password="testpass123",
            first_name="Member",
            last_name="User",
        )

        self.project = Project.objects.create(
            name="Internal Tool",
            description="Project for sync tests",
            owner=self.owner,
        )
        ProjectMember.objects.create(project=self.project, user=self.owner, role="admin")
        ProjectMember.objects.create(project=self.project, user=self.member, role="employee")

        self.group = Group.objects.create(
            name="Backend Team",
            description="Backend contributors",
            owner=self.owner,
        )
        GroupMember.objects.create(group=self.group, user=self.owner, role="admin")
        self.group.projects.add(self.project)

        self.task = Task.objects.create(
            name="Build API",
            description="Build the API layer",
            owner=self.owner,
            project=self.project,
            assigned_group=self.group,
        )

    def test_creating_group_member_syncs_group_members_and_group_tasks(self):
        GroupMember.objects.create(group=self.group, user=self.member, role="employee")

        self.assertTrue(self.group.members.filter(pk=self.member.pk).exists())
        self.assertTrue(self.task.assignees.filter(pk=self.member.pk).exists())

    def test_deleting_group_member_removes_user_from_group_members_and_group_tasks(self):
        membership = GroupMember.objects.create(
            group=self.group,
            user=self.member,
            role="employee",
        )
        self.task.assignees.add(self.member)

        membership.delete()

        self.assertFalse(self.group.members.filter(pk=self.member.pk).exists())
        self.assertFalse(self.task.assignees.filter(pk=self.member.pk).exists())
