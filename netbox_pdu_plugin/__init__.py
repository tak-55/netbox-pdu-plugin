"""
NetBox PDU Plugin

Plugin configuration for NetBox PDU Plugin.

For a complete list of PluginConfig attributes, see:
https://docs.netbox.dev/en/stable/plugins/development/#pluginconfig-attributes
"""

__author__ = "Takahiro Nagafuchi"
__email__ = "github@tak-lab.com"
__version__ = "0.2.0"


from netbox.plugins import PluginConfig


class PduConfig(PluginConfig):
    name = "netbox_pdu_plugin"
    verbose_name = "NetBox PDU Plugin"
    description = "NetBox plugin for Managed PDUs."
    author = "Takahiro Nagafuchi"
    author_email = "github@tak-lab.com"
    version = __version__
    base_url = "pdu"
    min_version = "4.5.0"
    max_version = "4.5.99"
    graphql_schema = "graphql.schema"
    queues = ["default"]

    def ready(self):
        super().ready()
        from . import jobs  # noqa: F401 — registers @system_job if metrics_poll_interval is set
        self._cleanup_stuck_jobs()

    def _cleanup_stuck_jobs(self):
        """Mark any stuck 'running' PDU jobs as errored on startup (e.g. after container restart or laptop sleep)."""
        try:
            from core.choices import JobStatusChoices
            from core.models import Job

            stuck = Job.objects.filter(
                name__in=["PDU Get Metrics", "PDU Sync"],
                status=JobStatusChoices.STATUS_RUNNING,
            )
            count = stuck.update(status=JobStatusChoices.STATUS_ERRORED)
            if count:
                import logging

                logging.getLogger(__name__).warning("Cleaned up %d stuck PDU job(s) on startup", count)
        except Exception:
            pass  # Do not block startup if cleanup fails


config = PduConfig
