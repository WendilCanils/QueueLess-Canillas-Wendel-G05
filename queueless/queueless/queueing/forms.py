from django import forms

from accounts.forms import BootstrapFormMixin

from .models import QueueTicket, Service


class PurposeCleanMixin:
    def clean_purpose(self):
        purpose = self.cleaned_data["purpose"].strip()
        if len(purpose) < 5:
            raise forms.ValidationError("Please describe your purpose in at least 5 characters.")
        return purpose


class TicketForm(BootstrapFormMixin, PurposeCleanMixin, forms.ModelForm):
    class Meta:
        model = QueueTicket
        fields = ("service", "purpose")
        widgets = {
            "purpose": forms.TextInput(attrs={"placeholder": "e.g. Request a copy of my grades"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["service"]
        field.queryset = Service.objects.filter(
            is_available=True, office__is_active=True
        ).select_related("office")
        field.empty_label = "Select a service"
        field.label_from_instance = lambda s: f"{s.office.name} - {s.name}"
        field.widget.attrs["class"] = "form-select"


class TicketUpdateForm(BootstrapFormMixin, PurposeCleanMixin, forms.ModelForm):
    class Meta:
        model = QueueTicket
        fields = ("purpose",)


class ServiceForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "description", "is_available")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, office=None, **kwargs):
        self.office = office
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        duplicates = Service.objects.filter(office=self.office, name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Your office already has a service with this name.")
        return name