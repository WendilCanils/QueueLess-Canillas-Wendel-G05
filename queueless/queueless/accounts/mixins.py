from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from .roles import dashboard_url_for, get_role


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Logged-out users go to login. Users with the wrong role go to their own dashboard."""
    required_role = None

    def test_func(self):
        return get_role(self.request.user) == self.required_role

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "You do not have access to that page.")
        return redirect(dashboard_url_for(self.request.user))