from django.contrib import messages
from django.shortcuts import redirect

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile
from accounts.roles import get_profile, get_role


class StudentRequiredMixin(RoleRequiredMixin):
    required_role = Profile.STUDENT


class StaffOfficeMixin(RoleRequiredMixin):
    """Staff only. Also loads the office the staff member manages."""
    required_role = Profile.STAFF
    office = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and get_role(request.user) == Profile.STAFF:
            self.office = get_profile(request.user).office
            if self.office is None:
                messages.warning(
                    request, "Your account is not assigned to an office yet. Ask an administrator."
                )
                return redirect("dashboard:staff")
        return super().dispatch(request, *args, **kwargs)