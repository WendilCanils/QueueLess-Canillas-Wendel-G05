from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import LoginForm, ProfileForm, SignUpForm
from .roles import dashboard_url_for


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")
    success_message = "Your account was created successfully. You can now log in."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(dashboard_url_for(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, "Registration failed. Please fix the errors below.")
        return super().form_invalid(form)


class RoleLoginView(SuccessMessageMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    success_message = "Welcome back, %(username)s!"

    def get_success_url(self):
        # Go to ?next= if present, otherwise to the dashboard for the user's role.
        return self.get_redirect_url() or dashboard_url_for(self.request.user)


class SignOutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been logged out.")
        return response


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
    success_message = "Your profile was updated."

    def get_object(self, queryset=None):
        # Always the logged-in user. There is no pk in the URL,
        # so nobody can open or edit another user's profile.
        return self.request.user

    def form_invalid(self, form):
        messages.error(self.request, "Could not save your profile. Please fix the errors below.")
        return super().form_invalid(form)