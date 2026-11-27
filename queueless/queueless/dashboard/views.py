from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile
from accounts.roles import dashboard_url_for, get_profile
from queueing.models import QueueTicket


@login_required
def home(request):
    """Sends the user to the dashboard for their role."""
    return redirect(dashboard_url_for(request.user))


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/student.html"
    required_role = Profile.STUDENT

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mine = QueueTicket.objects.filter(student=self.request.user).select_related(
            "office", "service"
        )
        ctx["active_ticket"] = mine.filter(
            queue_date=timezone.localdate(), status__in=QueueTicket.ACTIVE_STATUSES
        ).first()
        ctx["recent_tickets"] = mine.order_by("-created_at")[:5]
        return ctx


class StaffDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/staff.html"
    required_role = Profile.STAFF

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        office = get_profile(self.request.user).office
        ctx["office"] = office
        if office:
            today = QueueTicket.objects.filter(
                office=office, queue_date=timezone.localdate()
            ).select_related("student", "service")
            ctx["now_serving"] = today.filter(status=QueueTicket.SERVING)
            ctx["waiting_count"] = today.filter(status=QueueTicket.WAITING).count()
            ctx["completed_count"] = today.filter(status=QueueTicket.COMPLETED).count()
        return ctx