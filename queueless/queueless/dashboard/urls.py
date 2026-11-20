from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("student/", views.StudentDashboardView.as_view(), name="student"),
    path("staff/", views.StaffDashboardView.as_view(), name="staff"),
]