from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('governance', '0024_demande_avenue_rue_demande_commune_demande_district_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupecible',
            name='mission',
            field=models.TextField(blank=True),
        ),
    ]
