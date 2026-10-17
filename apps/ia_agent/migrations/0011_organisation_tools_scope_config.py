from django.db import migrations


NEW_TOOLS = ['get_organisation_mapping', 'get_experts_classification']


def add_organisation_tools(apps, schema_editor):
    AgentScopeConfig = apps.get_model('ia_agent', 'AgentScopeConfig')
    for config in AgentScopeConfig.objects.exclude(allowed_tools=None):
        tools = list(config.allowed_tools or [])
        changed = False
        for name in NEW_TOOLS:
            if name not in tools:
                tools.append(name)
                changed = True
        if changed:
            config.allowed_tools = tools
            config.save(update_fields=['allowed_tools'])


def remove_organisation_tools(apps, schema_editor):
    AgentScopeConfig = apps.get_model('ia_agent', 'AgentScopeConfig')
    for config in AgentScopeConfig.objects.exclude(allowed_tools=None):
        tools = [name for name in (config.allowed_tools or []) if name not in NEW_TOOLS]
        config.allowed_tools = tools
        config.save(update_fields=['allowed_tools'])


class Migration(migrations.Migration):

    dependencies = [
        ('ia_agent', '0010_alter_agentsession_provider'),
    ]

    operations = [
        migrations.RunPython(add_organisation_tools, remove_organisation_tools),
    ]
