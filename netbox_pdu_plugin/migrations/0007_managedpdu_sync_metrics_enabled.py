from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_pdu_plugin", "0006_managedpdu_pdu_name_alter_managedpdu_verify_ssl"),
    ]

    operations = [
        migrations.AddField(
            model_name="managedpdu",
            name="sync_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Include this PDU in periodic full sync jobs",
                verbose_name="Sync Enabled",
            ),
        ),
        migrations.AddField(
            model_name="managedpdu",
            name="metrics_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Include this PDU in periodic metrics polling jobs",
                verbose_name="Metrics Enabled",
            ),
        ),
    ]
