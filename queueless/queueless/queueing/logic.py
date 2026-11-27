from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import Office, QueueTicket, Service


class QueueError(Exception):
    """A queue rule was broken. The message is safe to show to the user."""


@transaction.atomic
def create_ticket(student, service, purpose):
    office = Office.objects.select_for_update().get(pk=service.office_id)
    service = Service.objects.get(pk=service.pk)

    if not office.is_active:
        raise QueueError("This office is not accepting queue tickets right now.")
    if not service.is_available:
        raise QueueError("This service is not available right now.")

    today = timezone.localdate()
    has_active = QueueTicket.objects.filter(
        student=student, queue_date=today, status__in=QueueTicket.ACTIVE_STATUSES
    ).exists()
    if has_active:
        raise QueueError(
            "You already have an active ticket. Finish or cancel it before taking another one."
        )

    last = QueueTicket.objects.filter(office=office, queue_date=today).aggregate(
        m=Max("queue_number")
    )["m"] or 0
    return QueueTicket.objects.create(
        student=student,
        office=office,
        service=service,
        purpose=purpose,
        queue_date=today,
        queue_number=last + 1,
    )


@transaction.atomic
def cancel_ticket(ticket):
    ticket = QueueTicket.objects.select_for_update().get(pk=ticket.pk)
    if ticket.status != QueueTicket.WAITING:
        raise QueueError("Only waiting tickets can be cancelled.")
    ticket.status = QueueTicket.CANCELLED
    ticket.completed_at = timezone.now()
    ticket.save(update_fields=["status", "completed_at"])
    return ticket


@transaction.atomic
def call_next(staff, office):
    if QueueTicket.objects.filter(
        office=office, served_by=staff, status=QueueTicket.SERVING
    ).exists():
        raise QueueError("Complete or mark no-show on your current ticket before calling the next student.")

    ticket = (
        QueueTicket.objects.select_for_update(skip_locked=True)
        .filter(office=office, queue_date=timezone.localdate(), status=QueueTicket.WAITING)
        .order_by("queue_number")
        .first()
    )
    if ticket is None:
        raise QueueError("No students are waiting in the queue.")

    ticket.status = QueueTicket.SERVING
    ticket.served_by = staff
    ticket.called_at = timezone.now()
    ticket.save(update_fields=["status", "served_by", "called_at"])
    return ticket


@transaction.atomic
def finish_ticket(ticket, staff, new_status):
    ticket = QueueTicket.objects.select_for_update().get(pk=ticket.pk)
    if ticket.status != QueueTicket.SERVING or ticket.served_by_id != staff.pk:
        raise QueueError("You can only finish a ticket that you are currently serving.")
    ticket.status = new_status
    ticket.completed_at = timezone.now()
    ticket.save(update_fields=["status", "completed_at"])
    return ticket