from django.urls import reverse

from .models import Profile


def get_profile(user):
    """Return the user's profile, creating it if it doesn't exist yet."""
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"role": Profile.STAFF if user.is_superuser else Profile.STUDENT},
    )
    return profile


def get_role(user):
    return get_profile(user).role


def dashboard_url_for(user):
    if get_role(user) == Profile.STAFF:
        return reverse("dashboard:staff")
    return reverse("dashboard:student")