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

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"