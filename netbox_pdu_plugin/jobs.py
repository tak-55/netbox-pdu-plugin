import logging
import re
from datetime import UTC, datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .backends import get_pdu_client
from .backends.base import PDUClientError
from .choices import OutletStatusChoices, SyncStatusChoices

logger = logging.getLogger(__name__)


def epoch_to_dt(epoch):
    """Convert epoch seconds to an aware datetime, or None."""
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(float(epoch), tz=UTC)
    except (ValueError, OSError):
        return None


def pdu_local_epoch_to_dt(epoch):
    """Convert PDU local-time epoch to an aware datetime, or None.

    Some PDU firmware (e.g. Raritan Xerus) encodes the local clock value
    as a Unix epoch without applying the UTC offset — i.e. the device clock
    shows 11:54 JST but the returned epoch corresponds to 11:54 UTC.
    This function interprets the numeric value as local time in Django's
    configured TIME_ZONE so the display matches what the PDU clock shows.
    """
    if epoch is None:
        return None
    try:
        naive = datetime.utcfromtimestamp(float(epoch))
        return timezone.make_aware(naive, timezone.get_current_timezone())
    except (ValueError, OSError):
        return None


def sync_managed_pdu(managed_pdu):
    """
    Full sync for a single ManagedPDU: hardware info, outlets, inlets, network interfaces.
    Returns (outlet_created, outlet_updated, inlet_created, inlet_updated).
    Raises PDUClientError on failure (caller is responsible for updating sync_status).
    """
    from dcim.models import PowerOutlet

    from . import models

    client = get_pdu_client(managed_pdu)

    with transaction.atomic():
        now = timezone.now()

        # Sync PDU hardware info
        pdu_info = client.get_pdu_info()
        managed_pdu.pdu_model = pdu_info.get("model", "")
        managed_pdu.serial_number = pdu_info.get("serial_number", "")
        managed_pdu.firmware_version = pdu_info.get("firmware_version", "")
        managed_pdu.rated_voltage = pdu_info.get("rated_voltage", "")
        managed_pdu.rated_current = pdu_info.get("rated_current", "")
        managed_pdu.rated_frequency = pdu_info.get("rated_frequency", "")
        managed_pdu.rated_power = pdu_info.get("rated_power", "")
        managed_pdu.hw_revision = pdu_info.get("hw_revision", "")
        managed_pdu.pdu_mac_address = pdu_info.get("pdu_mac_address", "")
        managed_pdu.dns_servers = pdu_info.get("dns_servers", "")
        managed_pdu.default_gateway = pdu_info.get("default_gateway", "")
        managed_pdu.device_time = pdu_local_epoch_to_dt(pdu_info.get("device_time_epoch"))
        managed_pdu.ntp_servers = pdu_info.get("ntp_servers", "")
        managed_pdu.pdu_name = pdu_info.get("pdu_name", "")

        # Sync serial number to Device
        serial = pdu_info.get("serial_number", "")
        if serial and managed_pdu.device.serial != serial:
            managed_pdu.device.serial = serial
            managed_pdu.device.save(update_fields=["serial"])
            logger.info("Updated Device serial [%s]: %s", managed_pdu.device, serial)

        models.PDUNetworkInterface.objects.filter(managed_pdu=managed_pdu).delete()
        for iface in pdu_info.get("network_interfaces", []):
            models.PDUNetworkInterface.objects.create(
                managed_pdu=managed_pdu,
                interface_name=iface.get("name", ""),
                mac_address=iface.get("mac_address", ""),
                ip_address=iface.get("ip_address", ""),
                config_method=iface.get("config_method", ""),
                link_speed=iface.get("link_speed", ""),
            )

        # Sync outlets
        outlet_data_list = client.get_all_outlet_data()
        outlet_created = 0
        outlet_updated = 0

        for outlet_data in outlet_data_list:
            outlet_number = outlet_data["outlet_number"]
            switching_state = outlet_data.get("switchingState", "unknown").lower()
            if switching_state == "on":
                status = OutletStatusChoices.ON
            elif switching_state == "off":
                status = OutletStatusChoices.OFF
            else:
                status = OutletStatusChoices.UNKNOWN

            obj, created = models.PDUOutlet.objects.update_or_create(
                managed_pdu=managed_pdu,
                outlet_number=outlet_number,
                defaults={
                    "outlet_name": outlet_data.get("name") or outlet_data.get("label", ""),
                    "status": status,
                    "current_a": outlet_data.get("current_a"),
                    "power_w": outlet_data.get("power_w"),
                    "voltage_v": outlet_data.get("voltage_v"),
                    "power_factor": outlet_data.get("power_factor"),
                    "energy_wh": outlet_data.get("energy_wh"),
                    "energy_reset_at": epoch_to_dt(outlet_data.get("energy_reset_epoch")),
                    "last_updated_from_pdu": now,
                },
            )
            if created:
                outlet_created += 1
            else:
                outlet_updated += 1

        # Sync connected_device from NetBox PowerOutlet cable connections
        nb_outlets = PowerOutlet.objects.filter(device=managed_pdu.device)
        for nb_outlet in nb_outlets:
            m = re.search(r"\d+", nb_outlet.name)
            if not m:
                continue
            outlet_num = int(m.group())
            peers = nb_outlet.link_peers
            connected = peers[0].device if peers else None
            models.PDUOutlet.objects.filter(
                managed_pdu=managed_pdu,
                outlet_number=outlet_num,
            ).update(connected_device=connected)

        # Sync inlets
        inlet_data_list = client.get_all_inlet_data()
        inlet_created = 0
        inlet_updated = 0

        for inlet_data in inlet_data_list:
            obj, created = models.PDUInlet.objects.update_or_create(
                managed_pdu=managed_pdu,
                inlet_number=inlet_data["inlet_number"],
                defaults={
                    "inlet_name": inlet_data.get("name", ""),
                    "current_a": inlet_data.get("current_a"),
                    "power_w": inlet_data.get("power_w"),
                    "apparent_power_va": inlet_data.get("apparent_power_va"),
                    "voltage_v": inlet_data.get("voltage_v"),
                    "power_factor": inlet_data.get("power_factor"),
                    "frequency_hz": inlet_data.get("frequency_hz"),
                    "energy_wh": inlet_data.get("energy_wh"),
                    "energy_reset_at": epoch_to_dt(inlet_data.get("energy_reset_epoch")),
                    "last_updated_from_pdu": now,
                },
            )
            if created:
                inlet_created += 1
            else:
                inlet_updated += 1

        managed_pdu.last_synced = now
        managed_pdu.sync_status = SyncStatusChoices.SUCCESS
        managed_pdu.save()

    return outlet_created, outlet_updated, inlet_created, inlet_updated


def update_outlet_status(outlet_pk, api_url, username, password, verify_ssl, outlet_index):
    """
    Background job: fetch outlet power state from PDU and save to DB.
    Intended to be enqueued after a power cycle command.
    """
    from .models import PDUOutlet

    try:
        outlet = PDUOutlet.objects.get(pk=outlet_pk)
        client = get_pdu_client(outlet.managed_pdu)
        new_state = client.get_outlet_power_state_by_index(outlet_index)
        state_map = {"on": OutletStatusChoices.ON, "off": OutletStatusChoices.OFF}

        outlet.status = state_map.get(new_state, OutletStatusChoices.UNKNOWN)
        outlet.last_updated_from_pdu = timezone.now()
        outlet.save()

        logger.info("Background status update for outlet pk=%s: %s", outlet_pk, new_state)
    except Exception as e:
        logger.error("Background status update failed for outlet pk=%s: %s", outlet_pk, e)


def fetch_pdu_metrics(managed_pdu):
    """
    Fetch Prometheus metrics for a single ManagedPDU and save to DB.
    Returns (outlet_updated, inlet_updated, ocp_updated) counts.
    Raises PDUClientError if the backend does not support Prometheus metrics or fetch fails.
    """
    from . import models

    client = get_pdu_client(managed_pdu)
    if not client.supports_prometheus_metrics:
        raise PDUClientError("Backend does not support Prometheus metrics")

    now = timezone.now()
    data = client.get_all_metrics_prometheus()

    with transaction.atomic():
        outlet_updated = 0
        for outlet_data in data.get("outlets", []):
            update_fields = {
                "current_a": outlet_data.get("current_a"),
                "power_w": outlet_data.get("power_w"),
                "apparent_power_va": outlet_data.get("apparent_power_va"),
                "voltage_v": outlet_data.get("voltage_v"),
                "power_factor": outlet_data.get("power_factor"),
                "energy_wh": outlet_data.get("energy_wh"),
                "last_updated_from_pdu": now,
            }
            if outlet_data.get("name"):
                update_fields["outlet_name"] = outlet_data["name"]
            outlet_updated += models.PDUOutlet.objects.filter(
                managed_pdu=managed_pdu,
                outlet_number=outlet_data["outlet_number"],
            ).update(**update_fields)

        inlet_updated = 0
        for inlet_data in data.get("inlets", []):
            inlet_number = inlet_data["inlet_number"]
            update_fields = {
                "current_a": inlet_data.get("current_a"),
                "power_w": inlet_data.get("power_w"),
                "apparent_power_va": inlet_data.get("apparent_power_va"),
                "voltage_v": inlet_data.get("voltage_v"),
                "power_factor": inlet_data.get("power_factor"),
                "frequency_hz": inlet_data.get("frequency_hz"),
                "energy_wh": inlet_data.get("energy_wh"),
                # 3-phase poleline and unbalance
                "poleline_l1_current_a": inlet_data.get("poleline_l1_current_a"),
                "poleline_l2_current_a": inlet_data.get("poleline_l2_current_a"),
                "poleline_l3_current_a": inlet_data.get("poleline_l3_current_a"),
                "unbalanced_current_pct": inlet_data.get("unbalanced_current_pct"),
                "unbalanced_ll_current_pct": inlet_data.get("unbalanced_ll_current_pct"),
                "unbalanced_ll_voltage_pct": inlet_data.get("unbalanced_ll_voltage_pct"),
                "last_updated_from_pdu": now,
            }
            if inlet_data.get("name"):
                update_fields["inlet_name"] = inlet_data["name"]
            inlet_updated += models.PDUInlet.objects.filter(
                managed_pdu=managed_pdu,
                inlet_number=inlet_number,
            ).update(**update_fields)

            # Linepairs: replace entirely (delete + recreate)
            models.PDUInletLinePair.objects.filter(
                managed_pdu=managed_pdu,
                inlet_number=inlet_number,
            ).delete()
            for lp in inlet_data.get("linepairs", []):
                models.PDUInletLinePair.objects.create(
                    managed_pdu=managed_pdu,
                    inlet_number=inlet_number,
                    line_pair=lp["line_pair"],
                    voltage_v=lp.get("voltage_v"),
                    current_a=lp.get("current_a"),
                    power_w=lp.get("power_w"),
                    apparent_power_va=lp.get("apparent_power_va"),
                    power_factor=lp.get("power_factor"),
                    energy_wh=lp.get("energy_wh"),
                    last_updated_from_pdu=now,
                )

        ocp_updated = 0
        for ocp_data in data.get("ocps", []):
            models.PDUOverCurrentProtector.objects.update_or_create(
                managed_pdu=managed_pdu,
                ocp_id=ocp_data["ocp_id"],
                defaults={
                    "rating_current_a": ocp_data.get("rating_current_a"),
                    "current_a": ocp_data.get("current_a"),
                    "poleline_l1_current_a": ocp_data.get("poleline_l1_current_a"),
                    "poleline_l2_current_a": ocp_data.get("poleline_l2_current_a"),
                    "poleline_l3_current_a": ocp_data.get("poleline_l3_current_a"),
                    "tripped": ocp_data.get("tripped"),
                    "last_updated_from_pdu": now,
                },
            )
            ocp_updated += 1

    managed_pdu.last_metrics_fetched = now
    managed_pdu.metrics_status = SyncStatusChoices.SUCCESS
    managed_pdu.save(update_fields=["last_metrics_fetched", "metrics_status"])

    return outlet_updated, inlet_updated, ocp_updated


_plugin_config = settings.PLUGINS_CONFIG.get("netbox_pdu_plugin", {})
_metrics_interval = _plugin_config.get("metrics_poll_interval", 0)
_sync_interval = _plugin_config.get("sync_poll_interval", 0)

if _metrics_interval > 0 or _sync_interval > 0:
    from netbox.jobs import JobFailed, JobRunner, system_job

if _metrics_interval > 0:

    @system_job(interval=_metrics_interval)
    class PDUGetMetricsJob(JobRunner):
        class Meta:
            name = "PDU Get Metrics"

        def run(self, *args, **kwargs):
            from . import models

            pdus = models.ManagedPDU.objects.filter(metrics_enabled=True)
            success, failed = 0, 0
            for pdu in pdus:
                try:
                    outlet_updated, inlet_updated, ocp_updated = fetch_pdu_metrics(pdu)
                    self.logger.info(
                        f"Metrics fetched [{pdu}]: outlets={outlet_updated} inlets={inlet_updated} ocps={ocp_updated}"
                    )
                    success += 1
                except Exception as e:
                    self.logger.error(f"Metrics fetch failed [{pdu}]: {e}")
                    pdu.metrics_status = SyncStatusChoices.FAILED
                    pdu.save(update_fields=["metrics_status"])
                    failed += 1
            self.logger.info(f"Periodic metrics complete: {success} OK, {failed} failed")
            if failed > 0 and success == 0:
                raise JobFailed(f"All {failed} PDU(s) failed to fetch metrics")
            elif failed > 0:
                raise Exception(f"{failed} PDU(s) failed to fetch metrics ({success} succeeded)")


if _sync_interval > 0:

    @system_job(interval=_sync_interval)
    class PDUSyncJob(JobRunner):
        class Meta:
            name = "PDU Sync"

        def run(self, *args, **kwargs):
            from . import models

            pdus = models.ManagedPDU.objects.filter(sync_enabled=True)
            success, failed = 0, 0
            for pdu in pdus:
                try:
                    outlet_created, outlet_updated, inlet_created, inlet_updated = sync_managed_pdu(pdu)
                    self.logger.info(
                        f"Sync complete [{pdu}]: outlets(created={outlet_created}, updated={outlet_updated})"
                        f" inlets(created={inlet_created}, updated={inlet_updated})"
                    )
                    success += 1
                except Exception as e:
                    self.logger.error(f"Sync failed [{pdu}]: {e}")
                    pdu.sync_status = SyncStatusChoices.FAILED
                    pdu.save(update_fields=["sync_status"])
                    failed += 1
            self.logger.info(f"Periodic sync complete: {success} OK, {failed} failed")
            if failed > 0 and success == 0:
                raise JobFailed(f"All {failed} PDU(s) failed to sync")
            elif failed > 0:
                raise Exception(f"{failed} PDU(s) failed to sync ({success} succeeded)")
