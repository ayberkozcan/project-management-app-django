from .models import GroupInvite

def group_invites_notifications(request):
    if not request.user.is_authenticated:
        return {}
    
    invites = GroupInvite.objects.filter(
        invited_user=request.user,
        accepted__isnull=True
    ).select_related("group", "invited_by")

    return {
        "notifications_count": invites.count(),
        "notifications": [
            {
                "message": f"{invite.invited_by.username} invited you to {invite.group.name}",
                "link": "/groups/my-invites/",
                "time_since": invite.created_at
            }
            for invite in invites[:5]
        ]
    }