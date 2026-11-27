from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Prefetch, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ServiceForm, TicketForm, TicketUpdateForm
from .logic import QueueError, call_next, cancel_ticket, create_ticket, finish_ticket
from .mixins import StaffOfficeMixin, StudentRequiredMixin
from .models import Office, QueueTicket, Service


class TicketFilterMixin:
    """Optional ?status= and ?date= filters for ticket lists."""
    allowed_statuses = QueueTicket.STATUS_CHOICES

    def filter_tickets(self, qs):
        status = self.request.GET.get("status", "")
        if status not in dict(self.allowed_statuses):
            status = ""
        try:
            day = parse_date(self.request.GET.get("date", "") or "")
        except ValueError:
            day = None

        if status:
            qs = qs.filter(status=status)
        if day:
            qs = qs.filter(queue_date=day)

        params = {}
        if status:
            params["status"] = status
        if day:
            params["date"] = day.isoformat()
        self.filter_state = {
            "status_choices": self.allowed_statuses,
            "current_status": status,
            "current_date": day.isoformat() if day else "",
            "filter_query": ("&" + urlencode(params)) if params else "",
        }
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.filter_state)
        return ctx


# ---------------------------------------------------------------- Student

class OfficeListView(StudentRequiredMixin, ListView):
    template_name = "queueing/office_list.html"
    context_object_name = "offices"

    def get_queryset(self):
        today = timezone.localdate()
        return (
            Office.objects.filter(is_active=True)
            .annotate(
                waiting_count=Count(
                    "tickets",
                    filter=Q(tickets__queue_date=today, tickets__status=QueueTicket.WAITING),
                )
            )
            .prefetch_related(
                Prefetch("services", queryset=Service.objects.filter(is_available=True))
            )
        )


class TicketCreateView(StudentRequiredMixin, CreateView):
    model = QueueTicket
    form_class = TicketForm
    template_name = "queueing/ticket_form.html"

    def get_initial(self):
        initial = super().get_initial()
        service_id = self.request.GET.get("service", "")
        if service_id.isdigit():
            initial["service"] = int(service_id)
        return initial

    def form_valid(self, form):
        try:
            self.object = create_ticket(
                self.request.user, form.cleaned_data["service"], form.cleaned_data["purpose"]
            )
        except QueueError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Ticket {self.object.code} created. You are number {self.object.position()} in line.",
        )
        return redirect(self.object)

    def form_invalid(self, form):
        messages.error(self.request, "Could not create your ticket. Please check the errors below.")
        return super().form_invalid(form)


class TicketListView(StudentRequiredMixin, TicketFilterMixin, ListView):
    template_name = "queueing/ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        qs = QueueTicket.objects.filter(student=self.request.user).select_related(
            "office", "service"
        )
        return self.filter_tickets(qs).order_by("-created_at")


class TicketDetailView(StudentRequiredMixin, DetailView):
    template_name = "queueing/ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        # Only the student's own tickets. Anyone else's ticket gives a 404.
        return QueueTicket.objects.filter(student=self.request.user).select_related(
            "office", "service", "served_by"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ticket = self.object
        ctx["position"] = ticket.position()
        ctx["now_serving"] = (
            QueueTicket.objects.filter(
                office=ticket.office, queue_date=ticket.queue_date, status=QueueTicket.SERVING
            )
            .order_by("-called_at")
            .first()
        )
        return ctx


class TicketUpdateView(StudentRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = TicketUpdateForm
    template_name = "queueing/ticket_form.html"
    context_object_name = "ticket"
    success_message = "Your ticket was updated."

    def get_queryset(self):
        return QueueTicket.objects.filter(student=self.request.user, status=QueueTicket.WAITING)

    def form_invalid(self, form):
        messages.error(self.request, "Could not update your ticket. Please check the errors below.")
        return super().form_invalid(form)


class TicketCancelView(StudentRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        ticket = get_object_or_404(QueueTicket, pk=pk, student=request.user)
        try:
            cancel_ticket(ticket)
        except QueueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Ticket {ticket.code} was cancelled.")
        return redirect("queueing:my_tickets")


class TicketDeleteView(StudentRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "queueing/ticket_confirm_delete.html"
    context_object_name = "ticket"
    success_url = reverse_lazy("queueing:my_tickets")
    success_message = "The ticket was removed from your history."

    def get_queryset(self):
        # Only finished tickets can be deleted from history.
        return QueueTicket.objects.filter(
            student=self.request.user, status__in=QueueTicket.FINISHED_STATUSES
        )


# ------------------------------------------------------------------ Staff

class StaffQueueView(StaffOfficeMixin, TemplateView):
    template_name = "queueing/staff_queue.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = QueueTicket.objects.filter(
            office=self.office, queue_date=timezone.localdate()
        ).select_related("student", "service", "served_by")
        ctx["office"] = self.office
        ctx["my_serving"] = today.filter(status=QueueTicket.SERVING, served_by=user)
        ctx["others_serving"] = today.filter(status=QueueTicket.SERVING).exclude(served_by=user)
        ctx["waiting"] = today.filter(status=QueueTicket.WAITING).order_by("queue_number")
        ctx["finished"] = today.filter(status__in=QueueTicket.FINISHED_STATUSES).order_by(
            "-completed_at"
        )[:10]
        return ctx


class CallNextView(StaffOfficeMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        try:
            ticket = call_next(request.user, self.office)
        except QueueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Now serving {ticket.code}.")
        return redirect("queueing:staff_queue")


class FinishTicketView(StaffOfficeMixin, View):
    http_method_names = ["post"]
    new_status = None
    success_text = ""

    def post(self, request, pk):
        ticket = get_object_or_404(QueueTicket, pk=pk, office=self.office)
        try:
            finish_ticket(ticket, request.user, self.new_status)
        except QueueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"{ticket.code} {self.success_text}")
        return redirect("queueing:staff_queue")


class StaffRecordsView(StaffOfficeMixin, TicketFilterMixin, ListView):
    template_name = "queueing/staff_records.html"
    context_object_name = "tickets"
    paginate_by = 15
    allowed_statuses = [
        c for c in QueueTicket.STATUS_CHOICES if c[0] in QueueTicket.FINISHED_STATUSES
    ]

    def get_queryset(self):
        qs = QueueTicket.objects.filter(
            office=self.office, status__in=QueueTicket.FINISHED_STATUSES
        ).select_related("student", "service", "served_by")
        return self.filter_tickets(qs).order_by("-queue_date", "-queue_number")


class ServiceListView(StaffOfficeMixin, ListView):
    template_name = "queueing/service_list.html"
    context_object_name = "services"

    def get_queryset(self):
        return Service.objects.filter(office=self.office)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["office"] = self.office
        return ctx


class ServiceFormMixin:
    form_class = ServiceForm
    template_name = "queueing/service_form.html"
    success_url = reverse_lazy("queueing:service_list")

    def get_queryset(self):
        return Service.objects.filter(office=self.office)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["office"] = self.office
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, "Could not save the service. Please check the errors below.")
        return super().form_invalid(form)


class ServiceCreateView(StaffOfficeMixin, ServiceFormMixin, SuccessMessageMixin, CreateView):
    success_message = "Service added."

    def form_valid(self, form):
        form.instance.office = self.office
        return super().form_valid(form)


class ServiceUpdateView(StaffOfficeMixin, ServiceFormMixin, SuccessMessageMixin, UpdateView):
    success_message = "Service updated."


class ServiceDeleteView(StaffOfficeMixin, DeleteView):
    template_name = "queueing/service_confirm_delete.html"
    context_object_name = "service"
    success_url = reverse_lazy("queueing:service_list")

    def get_queryset(self):
        return Service.objects.filter(office=self.office)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "This service already has queue tickets, so it cannot be deleted. "
                "Mark it as unavailable instead.",
            )
            return redirect(self.success_url)
        messages.success(self.request, "Service deleted.")
        return response