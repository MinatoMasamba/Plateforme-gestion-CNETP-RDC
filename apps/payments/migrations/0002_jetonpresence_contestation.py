from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='jetonpresence',
            name='contestation_status',
            field=models.CharField(
                choices=[
                    ('NONE', 'Aucune'),
                    ('PENDING', 'En attente d’instruction'),
                    ('ACCEPTED', 'Contestation acceptée'),
                    ('REJECTED', 'Contestation rejetée'),
                ],
                default='NONE',
                max_length=20,
                verbose_name='Statut de la contestation',
            ),
        ),
        migrations.AddField(
            model_name='jetonpresence',
            name='contestation_motif',
            field=models.TextField(blank=True, verbose_name='Motif de la contestation'),
        ),
        migrations.AddField(
            model_name='jetonpresence',
            name='contestation_created_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Contesté le'),
        ),
        migrations.AddField(
            model_name='jetonpresence',
            name='contestation_resolution',
            field=models.TextField(blank=True, verbose_name='Décision d’instruction'),
        ),
        migrations.AddField(
            model_name='jetonpresence',
            name='contestation_resolved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Instruit le'),
        ),
        migrations.AddField(
            model_name='jetonpresence',
            name='contestation_resolved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='jeton_contestations_resolved',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Instruit par',
            ),
        ),
    ]
