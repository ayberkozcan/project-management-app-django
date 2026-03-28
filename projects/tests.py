from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from groups.models import Group, GroupMember
from projects.models import ActivityLog, Comment, Project, ProjectMember
from tasks.models import Task


class DeletionCascadeTests(TestCase):
    def setUp(self):
        cache.clear()
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

    def test_deleting_project_removes_related_tasks_memberships_comments_and_logs(self):
        project = Project.objects.create(
            name="Website Revamp",
            description="Main project",
            owner=self.owner,
        )
        ProjectMember.objects.create(project=project, user=self.owner, role="admin")
        ProjectMember.objects.create(project=project, user=self.member, role="employee")

        task = Task.objects.create(
            name="Landing Page",
            description="Create the landing page",
            owner=self.owner,
            project=project,
        )
        task.assignees.add(self.member)

        Comment.objects.create(
            author=self.owner,
            project=project,
            task=task,
            content="Please prioritize this task.",
        )
        ActivityLog.objects.create(
            actor=self.owner,
            project=project,
            task=task,
            action_type=ActivityLog.ACTION_TASK,
            description="created task Landing Page",
        )

        project.delete()

        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertEqual(ProjectMember.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(ActivityLog.objects.count(), 0)
        self.assertEqual(self.member.assigned_tasks.count(), 0)

    def test_deleting_group_removes_related_group_data_and_group_assigned_tasks(self):
        project = Project.objects.create(
            name="Mobile App",
            description="Project with group",
            owner=self.owner,
        )
        ProjectMember.objects.create(project=project, user=self.owner, role="admin")
        ProjectMember.objects.create(project=project, user=self.member, role="employee")

        group = Group.objects.create(
            name="Frontend Team",
            description="Frontend contributors",
            owner=self.owner,
        )
        GroupMember.objects.create(group=group, user=self.owner, role="admin")
        GroupMember.objects.create(group=group, user=self.member, role="employee")
        group.members.add(self.owner, self.member)
        group.projects.add(project)

        task = Task.objects.create(
            name="Build UI",
            description="Implement the first screen",
            owner=self.owner,
            project=project,
            assigned_group=group,
        )
        task.assignees.add(self.member)

        Comment.objects.create(
            author=self.owner,
            project=project,
            group=group,
            task=task,
            content="Group level update",
        )
        ActivityLog.objects.create(
            actor=self.owner,
            project=project,
            group=group,
            task=task,
            action_type=ActivityLog.ACTION_GROUP,
            description="assigned group Frontend Team to the project",
        )

        group.delete()

        self.assertFalse(Group.objects.filter(pk=group.pk).exists())
        self.assertEqual(GroupMember.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(ActivityLog.objects.count(), 0)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertEqual(self.member.assigned_tasks.count(), 0)
        self.assertEqual(project.assigned_groups.count(), 0)


class AuthorizationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = Account.objects.create_user(
            email="owner-auth@example.com",
            username="owner_auth",
            password="testpass123",
            first_name="Owner",
            last_name="Auth",
        )
        self.member = Account.objects.create_user(
            email="member-auth@example.com",
            username="member_auth",
            password="testpass123",
            first_name="Member",
            last_name="Auth",
        )
        self.outsider = Account.objects.create_user(
            email="outsider-auth@example.com",
            username="outsider_auth",
            password="testpass123",
            first_name="Outsider",
            last_name="Auth",
        )

        self.project = Project.objects.create(
            name="Secure Project",
            description="Authorization checks",
            owner=self.owner,
        )
        ProjectMember.objects.create(project=self.project, user=self.owner, role="admin")
        ProjectMember.objects.create(project=self.project, user=self.member, role="employee")

        self.group = Group.objects.create(
            name="Secure Group",
            description="Restricted group",
            owner=self.owner,
        )
        GroupMember.objects.create(group=self.group, user=self.owner, role="admin")
        GroupMember.objects.create(group=self.group, user=self.member, role="employee")
        self.group.projects.add(self.project)

        self.task = Task.objects.create(
            name="Secure Task",
            description="Restricted task",
            owner=self.owner,
            project=self.project,
        )
        self.task.assignees.add(self.member)

        self.project_admin = Account.objects.create_user(
            email="project-admin@example.com",
            username="project_admin",
            password="testpass123",
            first_name="Project",
            last_name="Admin",
        )
        self.group_admin = Account.objects.create_user(
            email="group-admin@example.com",
            username="group_admin",
            password="testpass123",
            first_name="Group",
            last_name="Admin",
        )
        self.regular_member = Account.objects.create_user(
            email="regular-member@example.com",
            username="regular_member",
            password="testpass123",
            first_name="Regular",
            last_name="Member",
        )

        ProjectMember.objects.create(project=self.project, user=self.project_admin, role="admin")
        ProjectMember.objects.create(project=self.project, user=self.regular_member, role="employee")
        GroupMember.objects.create(group=self.group, user=self.group_admin, role="admin")
        GroupMember.objects.create(group=self.group, user=self.regular_member, role="employee")

    def test_outsider_cannot_access_project_views(self):
        self.client.force_login(self.outsider)

        protected_urls = {
            reverse("project_detail", kwargs={"pk": self.project.pk}): {404},
            reverse("project_members", kwargs={"project_id": self.project.pk}): {403},
            reverse("project_groups", kwargs={"project_id": self.project.pk}): {403},
            reverse("project_tasks", kwargs={"project_id": self.project.pk}): {403},
            reverse("project_comments", kwargs={"project_id": self.project.pk}): {403},
        }

        for url, allowed_statuses in protected_urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, allowed_statuses)

    def test_outsider_cannot_access_group_views(self):
        self.client.force_login(self.outsider)

        protected_urls = {
            reverse("group_detail", kwargs={"pk": self.group.pk}): {404},
            reverse("group_comments", kwargs={"group_id": self.group.pk}): {403},
            reverse("group_projects", kwargs={"group_id": self.group.pk}): {404},
            reverse("group_members", kwargs={"group_id": self.group.pk}): {403},
        }

        for url, allowed_statuses in protected_urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, allowed_statuses)

    def test_outsider_cannot_access_task_detail(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("tasks:task_detail", kwargs={"pk": self.task.pk}))

        self.assertEqual(response.status_code, 404)

    def test_only_project_owner_can_edit_or_delete_project(self):
        owner_edit = reverse("project_edit", kwargs={"pk": self.project.pk})
        owner_only_delete_project = Project.objects.create(
            name="Owner Delete Project",
            description="Delete permission test",
            owner=self.owner,
        )
        ProjectMember.objects.create(
            project=owner_only_delete_project,
            user=self.owner,
            role="admin",
        )
        owner_delete = reverse("project_delete", kwargs={"pk": owner_only_delete_project.pk})

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(owner_edit).status_code, 200)
        self.assertEqual(self.client.post(owner_delete).status_code, 302)
        self.assertFalse(Project.objects.filter(pk=owner_only_delete_project.pk).exists())

        self.client.force_login(self.project_admin)
        self.assertEqual(self.client.get(owner_edit).status_code, 404)
        self.assertEqual(self.client.get(owner_delete).status_code, 404)

    def test_project_owner_and_admin_can_manage_project_members(self):
        add_url = reverse("member_add", kwargs={"project_id": self.project.pk})
        remove_url = reverse(
            "member_remove",
            kwargs={"project_id": self.project.pk, "member_id": self.regular_member.pk},
        )

        self.client.force_login(self.project_admin)
        self.assertEqual(self.client.get(add_url).status_code, 200)
        self.assertEqual(self.client.post(remove_url).status_code, 302)

        ProjectMember.objects.create(project=self.project, user=self.regular_member, role="employee")

        self.client.force_login(self.regular_member)
        self.assertEqual(self.client.get(add_url).status_code, 403)
        self.assertEqual(self.client.post(remove_url).status_code, 403)

    def test_project_owner_and_admin_can_manage_tasks(self):
        project_add_task_url = reverse("task_add", kwargs={"project_id": self.project.pk})
        task_edit_url = reverse("task_edit", kwargs={"pk": self.task.pk})
        task_delete_url = reverse("tasks:task_delete", kwargs={"pk": self.task.pk})

        self.client.force_login(self.project_admin)
        self.assertEqual(self.client.get(project_add_task_url).status_code, 200)
        self.assertEqual(self.client.get(task_edit_url).status_code, 200)
        self.assertEqual(self.client.post(task_delete_url).status_code, 302)

        self.task = Task.objects.create(
            name="Secure Task Reloaded",
            description="Replacement task",
            owner=self.owner,
            project=self.project,
        )

        self.client.force_login(self.regular_member)
        self.assertEqual(self.client.get(project_add_task_url).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("task_edit", kwargs={"pk": self.task.pk})).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse("tasks:task_delete", kwargs={"pk": self.task.pk})).status_code,
            404,
        )

    def test_only_project_owner_and_admin_can_delete_project_comments(self):
        comment = Comment.objects.create(
            author=self.member,
            project=self.project,
            content="Temporary project comment",
        )
        delete_url = reverse(
            "project_comment_delete",
            kwargs={"project_id": self.project.pk, "comment_id": comment.pk},
        )

        self.client.force_login(self.project_admin)
        self.assertEqual(self.client.post(delete_url).status_code, 302)

        comment = Comment.objects.create(
            author=self.member,
            project=self.project,
            content="Temporary project comment 2",
        )
        delete_url = reverse(
            "project_comment_delete",
            kwargs={"project_id": self.project.pk, "comment_id": comment.pk},
        )

        self.client.force_login(self.regular_member)
        self.assertEqual(self.client.post(delete_url).status_code, 403)

    def test_only_group_owner_can_edit_or_delete_group(self):
        edit_url = reverse("group_edit", kwargs={"pk": self.group.pk})
        owner_only_delete_group = Group.objects.create(
            name="Owner Delete Group",
            description="Delete permission test",
            owner=self.owner,
        )
        GroupMember.objects.create(
            group=owner_only_delete_group,
            user=self.owner,
            role="admin",
        )
        delete_url = reverse("group_delete", kwargs={"pk": owner_only_delete_group.pk})

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertFalse(Group.objects.filter(pk=owner_only_delete_group.pk).exists())

        self.client.force_login(self.group_admin)
        self.assertEqual(self.client.get(edit_url).status_code, 404)
        self.assertEqual(self.client.get(delete_url).status_code, 404)

    def test_group_owner_and_admin_can_manage_group_members(self):
        add_url = reverse("group_member_add", kwargs={"group_id": self.group.pk})
        remove_url = reverse(
            "group_member_remove",
            kwargs={"group_id": self.group.pk, "member_id": self.regular_member.pk},
        )

        self.client.force_login(self.group_admin)
        self.assertEqual(self.client.get(add_url).status_code, 200)
        self.assertEqual(self.client.post(remove_url).status_code, 302)

        GroupMember.objects.create(group=self.group, user=self.regular_member, role="employee")

        self.client.force_login(self.regular_member)
        self.assertEqual(self.client.get(add_url).status_code, 403)
        self.assertEqual(self.client.post(remove_url).status_code, 403)


class RateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = Account.objects.create_user(
            email="owner-rate@example.com",
            username="owner_rate",
            password="testpass123",
            first_name="Owner",
            last_name="Rate",
        )
        self.project = Project.objects.create(
            name="Rate Limited Project",
            description="Rate limit checks",
            owner=self.owner,
        )
        ProjectMember.objects.create(project=self.project, user=self.owner, role="admin")

    def test_project_comments_are_rate_limited(self):
        self.client.force_login(self.owner)
        url = reverse("project_detail", kwargs={"pk": self.project.pk})

        for index in range(20):
            response = self.client.post(url, {"content": f"Comment {index}"})
            self.assertEqual(response.status_code, 302)

        response = self.client.post(url, {"content": "Comment overflow"})

        self.assertEqual(response.status_code, 429)
