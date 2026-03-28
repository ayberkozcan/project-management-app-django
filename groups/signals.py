from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from groups.models import GroupMember
from tasks.models import Task


@receiver(post_save, sender=GroupMember)
def sync_group_member_on_create(sender, instance, created, **kwargs):
    if not created:
        return

    group = instance.group
    user = instance.user

    group.members.add(user)
    for task in Task.objects.filter(assigned_group=group):
        task.assignees.add(user)


@receiver(post_delete, sender=GroupMember)
def sync_group_member_on_delete(sender, instance, **kwargs):
    group = instance.group
    user = instance.user

    group.members.remove(user)
    for task in Task.objects.filter(assigned_group=group, assignees=user):
        task.assignees.remove(user)
