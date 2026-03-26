from projects.models import ActivityLog


def log_activity(*, actor, project, action_type, description, group=None, task=None):
    return ActivityLog.objects.create(
        actor=actor,
        project=project,
        group=group,
        task=task,
        action_type=action_type,
        description=description,
    )
