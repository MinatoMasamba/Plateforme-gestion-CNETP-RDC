from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('governance', '0047_stgedanomaly_kind_stgedanomaly_recipient')]

    operations = [
        migrations.AddField(
            model_name='stgedindexation',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
