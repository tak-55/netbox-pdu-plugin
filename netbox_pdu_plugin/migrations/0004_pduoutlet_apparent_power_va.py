from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_pdu_plugin", "0003_pduinlet_poleline_l1_current_a_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="pduoutlet",
            name="apparent_power_va",
            field=models.FloatField(
                blank=True,
                help_text="Apparent power (volt-amperes)",
                null=True,
                verbose_name="Apparent Power (VA)",
            ),
        ),
    ]
