from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ia_agent', '0007_agentsession_provider_deepseek'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RAGDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL)),
                ('source_kind', models.CharField(choices=[('DOCUMENT', 'Document de la plateforme'), ('NORME', 'Norme'), ('NORME_VERSION', 'Version de norme'), ('EXPERT_CV', 'CV expert')], max_length=20)),
                ('source_key', models.CharField(max_length=180, unique=True)),
                ('title', models.CharField(max_length=500)),
                ('mime_type', models.CharField(blank=True, max_length=120)),
                ('content_hash', models.CharField(blank=True, max_length=64)),
                ('status', models.CharField(choices=[('INDEXED', 'Indexé'), ('EMPTY', 'Sans texte exploitable'), ('ERROR', 'Erreur d extraction')], default='INDEXED', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('extraction_error', models.TextField(blank=True)),
                ('indexed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Source RAG',
                'verbose_name_plural': 'Sources RAG',
                'indexes': [
                    models.Index(fields=['source_kind', 'status'], name='ia_agent_ra_source__a6714e_idx'),
                    models.Index(fields=['content_hash'], name='ia_agent_ra_content_55696e_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='RAGChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordinal', models.PositiveIntegerField()),
                ('content', models.TextField()),
                ('page_number', models.PositiveIntegerField(blank=True, null=True)),
                ('section', models.CharField(blank=True, max_length=500)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='ia_agent.ragdocument')),
            ],
            options={
                'verbose_name': 'Passage RAG',
                'verbose_name_plural': 'Passages RAG',
                'ordering': ['document_id', 'ordinal'],
                'indexes': [
                    models.Index(fields=['document', 'page_number'], name='ia_agent_ra_documen_ca1c1d_idx'),
                ],
                'constraints': [
                    models.UniqueConstraint(fields=('document', 'ordinal'), name='unique_rag_chunk_order'),
                ],
            },
        ),
    ]
