from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile
from accounts.roles import dashboard_url_for


@login_required
def home(request):
    """Sends the user to the dashboard for their role."""
    return redirect(dashboard_url_for(request.user))


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/student.html"
    required_role = Profile.STUDENT


class StaffDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/staff.html"
    required_role = Profile.STAFF