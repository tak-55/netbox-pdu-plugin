from dcim.models import Device, DeviceRole
from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet

from .choices import OutletStatusChoices, SyncStatusChoices
from .models import ManagedPDU, PDUInlet, PDUOutlet


class ManagedPDUForm(NetBoxModelForm):
    device_role = DynamicModelChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
        label=_("Device Role (filter)"),
        help_text=_("Filter device list by role"),
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        help_text=_("Select the PDU device registered in NetBox"),
        query_params={"role_id": "$device_role"},
    )
    comments = CommentField()

    fieldsets = (
        FieldSet("device_role", "device", name="Device"),
        FieldSet("vendor", "api_url", "api_username", "api_password", "verify_ssl", name="Connection"),
        FieldSet("sync_enabled", "metrics_enabled", name="Polling"),
        FieldSet("comments", "tags", name="Other"),
    )

    class Meta:
        model = ManagedPDU
        fields = (
            "device",
            "vendor",
            "api_url",
            "api_username",
            "api_password",
            "verify_ssl",
            "sync_enabled",
            "metrics_enabled",
            "comments",
            "tags",
        )
        widgets = {
            "api_password": forms.PasswordInput(render_value=True),
        }


class ManagedPDUFilterForm(NetBoxModelFilterSetForm):
    model = ManagedPDU
    fieldsets = (
        FieldSet("q", "filter_id", "tag"),
        FieldSet("sync_status", name="Sync"),
    )
    sync_status = forms.MultipleChoiceField(
        choices=SyncStatusChoices,
        required=False,
        label=_("Sync Status"),
    )
    tag = TagFilterField(model)


class PDUOutletForm(NetBoxModelForm):
    managed_pdu = DynamicModelChoiceField(
        queryset=ManagedPDU.objects.all(),
        label=_("Managed PDU"),
    )
    device_role = DynamicModelChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
        label=_("Device Role (filter)"),
        help_text=_("Filter connected device list by role"),
    )
    connected_device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label=_("Connected Device"),
        help_text=_("Device connected to this outlet"),
        query_params={"role_id": "$device_role"},
    )
    comments = CommentField()

    class Meta:
        model = PDUOutlet
        fields = (
            "managed_pdu",
            "outlet_number",
            "outlet_name",
            "device_role",
            "connected_device",
            "comments",
            "tags",
        )


class PDUOutletFilterForm(NetBoxModelFilterSetForm):
    model = PDUOutlet
    fieldsets = (
        FieldSet("q", "filter_id", "tag"),
        FieldSet("managed_pdu_id", "status", name="Outlet"),
    )
    managed_pdu_id = DynamicModelMultipleChoiceField(
        queryset=ManagedPDU.objects.all(),
        required=False,
        label=_("Managed PDU"),
    )
    status = forms.MultipleChoiceField(
        choices=OutletStatusChoices,
        required=False,
        label=_("Status"),
    )
    tag = TagFilterField(model)


class PDUInletForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = PDUInlet
        fields = ("inlet_name", "comments", "tags")


class PDUInletFilterForm(NetBoxModelFilterSetForm):
    model = PDUInlet
    fieldsets = (
        FieldSet("q", "filter_id", "tag"),
        FieldSet("managed_pdu_id", name="Inlet"),
    )
    managed_pdu_id = DynamicModelMultipleChoiceField(
        queryset=ManagedPDU.objects.all(),
        required=False,
        label=_("Managed PDU"),
    )
    tag = TagFilterField(model)
