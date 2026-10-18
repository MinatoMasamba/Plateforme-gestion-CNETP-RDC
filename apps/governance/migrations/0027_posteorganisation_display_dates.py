from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('governance', '0026_alter_affectationsouscommission_source_kind'),
    ]

    operations = [
        migrations.AddField(
            model_name='posteorganisation',
            name='display_created_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de création affichée'),
        ),
        migrations.AddField(
            model_name='posteorganisation',
            name='display_updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de modification affichée'),
        ),
    ]
