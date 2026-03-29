from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_pdu_plugin", "0005_managedpdu_metrics_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="managedpdu",
            name="pdu_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Device name as configured on the PDU hardware",
                max_length=200,
                verbose_name="PDU Name",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="managedpdu",
            name="verify_ssl",
            field=models.BooleanField(
                default=False,
                help_text="Verify the SSL certificate when connecting via HTTPS",
                verbose_name="Verify SSL",
            ),
        ),
    ]
