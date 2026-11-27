from django.urls import path

from . import views
from .models import QueueTicket

app_name = "queueing"

urlpatterns = [
    # Student
    path("offices/", views.OfficeListView.as_view(), name="office_list"),
    path("tickets/", views.TicketListView.as_view(), name="my_tickets"),
    path("tickets/new/", views.TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/<int:pk>/", views.TicketDetailView.as_view(), name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.TicketUpdateView.as_view(), name="ticket_update"),
    path("tickets/<int:pk>/cancel/", views.TicketCancelView.as_view(), name="ticket_cancel"),
    path("tickets/<int:pk>/delete/", views.TicketDeleteView.as_view(), name="ticket_delete"),
    # Staff
    path("staff/queue/", views.StaffQueueView.as_view(), name="staff_queue"),
    path("staff/queue/call-next/", views.CallNextView.as_view(), name="call_next"),
    path(
        "staff/tickets/<int:pk>/complete/",
        views.FinishTicketView.as_view(
            new_status=QueueTicket.COMPLETED, success_text="was marked as completed."
        ),
        name="ticket_complete",
    ),
    path(
        "staff/tickets/<int:pk>/no-show/",
        views.FinishTicketView.as_view(
            new_status=QueueTicket.NO_SHOW, success_text="was marked as no-show."
        ),
        name="ticket_no_show",
    ),
    path("staff/records/", views.StaffRecordsView.as_view(), name="staff_records"),
    path("staff/services/", views.ServiceListView.as_view(), name="service_list"),
    path("staff/services/new/", views.ServiceCreateView.as_view(), name="service_create"),
    path("staff/services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service_update"),
    path("staff/services/<int:pk>/delete/", views.ServiceDeleteView.as_view(), name="service_delete"),
]