from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ia_agent', '0006_agentpostecontext_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentsession',
            name='provider',
            field=models.CharField(
                choices=[('deepseek', 'DeepSeek')],
                default='deepseek',
                max_length=20,
            ),
        ),
    ]
