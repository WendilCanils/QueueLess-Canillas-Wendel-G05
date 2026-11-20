from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import RegexValidator

from .roles import get_profile

User = get_user_model()

contact_validator = RegexValidator(
    r"^[0-9+()\-\s]{7,20}$",
    "Enter a valid contact number (digits, spaces, +, - and parentheses only).",
)


class BootstrapFormMixin:
    """Adds Bootstrap classes to every widget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs["class"] = css


class UniqueEmailMixin:
    """Rejects an email that another account already uses (case-insensitive)."""
    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        duplicates = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class SignUpForm(BootstrapFormMixin, UniqueEmailMixin, UserCreationForm):
    contact_number = forms.CharField(
        max_length=20, required=False, validators=[contact_validator]
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    field_order = [
        "username", "first_name", "last_name", "email",
        "contact_number", "password1", "password2",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True

    def save(self, commit=True):
        user = super().save(commit=commit)  # password is hashed here
        if commit:
            profile = get_profile(user)  # new accounts are always Students
            profile.contact_number = self.cleaned_data["contact_number"]
            profile.save()
        return user


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class ProfileForm(BootstrapFormMixin, UniqueEmailMixin, forms.ModelForm):
    contact_number = forms.CharField(
        max_length=20, required=False, validators=[contact_validator]
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True
        self.fields["contact_number"].initial = get_profile(self.instance).contact_number

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = get_profile(user)
            profile.contact_number = self.cleaned_data["contact_number"]
            profile.save()
        return user