from django.db import migrations


def seed_templates(apps, schema_editor):
    Template = apps.get_model('governance', 'STReportTemplate')
    definitions = [
        ('activity', 'Rapport d’activité', ['Objet du rapport', 'Activités réalisées', 'Résultats et livrables', 'Difficultés rencontrées', 'Recommandations et prochaines étapes']),
        ('meeting', 'Compte rendu de séance', ['Objet de la séance', 'Participants', 'Points examinés', 'Décisions et actions à suivre']),
        ('followup', 'Note de suivi', ['Objet du suivi', 'État d’avancement', 'Écarts et retards', 'Actions proposées']),
    ]
    for code, name, sections in definitions:
        Template.objects.get_or_create(system_code=code, defaults={'name': name, 'sections': [{'title': title, 'content': ''} for title in sections]})


class Migration(migrations.Migration):
    dependencies = [('governance', '0037_st_reports')]
    operations = [migrations.RunPython(seed_templates, migrations.RunPython.noop)]
