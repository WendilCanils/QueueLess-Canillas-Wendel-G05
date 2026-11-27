from django.conf import settings
from django.db import models


class Profile(models.Model):
    STUDENT = "student"
    STAFF = "staff"
    ROLE_CHOICES = [
        (STUDENT, "Student"),
        (STAFF, "Office Staff"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    contact_number = models.CharField(max_length=20, blank=True)
    office = models.ForeignKey(
        "queueing.Office",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_profiles",
        help_text="The office this staff member manages (staff only).",
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"