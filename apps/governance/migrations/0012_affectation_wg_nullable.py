from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('governance', '0011_platformfreeze'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affectation',
            name='wg',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='affectations',
                to='governance.wg',
            ),
        ),
    ]
