from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Office(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=6, unique=True, help_text="Ticket prefix, e.g. REG gives REG-001"
    )
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["office__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["office", "name"], name="unique_service_per_office")
        ]

    def __str__(self):
        return f"{self.office.code} - {self.name}"


class QueueTicket(models.Model):
    WAITING = "waiting"
    SERVING = "serving"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    STATUS_CHOICES = [
        (WAITING, "Waiting"),
        (SERVING, "Serving"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
        (NO_SHOW, "No-show"),
    ]
    ACTIVE_STATUSES = [WAITING, SERVING]
    FINISHED_STATUSES = [COMPLETED, CANCELLED, NO_SHOW]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="queue_tickets"
    )
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="tickets")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="tickets")
    queue_date = models.DateField(default=timezone.localdate)
    queue_number = models.PositiveIntegerField()
    purpose = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=WAITING)
    served_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="served_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["queue_date", "queue_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["office", "queue_date", "queue_number"],
                name="unique_ticket_number_per_office_day",
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.student}"

    @property
    def code(self):
        return f"{self.office.code}-{self.queue_number:03d}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    def get_absolute_url(self):
        return reverse("queueing:ticket_detail", kwargs={"pk": self.pk})

    def position(self):
        """1 = next in line. Only meaningful while the ticket is waiting."""
        if self.status != self.WAITING:
            return None
        ahead = QueueTicket.objects.filter(
            office=self.office,
            queue_date=self.queue_date,
            status=self.WAITING,
            queue_number__lt=self.queue_number,
        ).count()
        return ahead + 1