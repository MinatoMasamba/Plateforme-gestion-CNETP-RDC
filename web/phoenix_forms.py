from django import forms
from copy import deepcopy
import json
from django.db.models import Q
from apps.experts.models import Expert
from apps.norms.models import Norme
from apps.governance.models import Organe, PosteOrganisation, GroupeCible, MandatOrganisation, HabilitationAction, CircuitOrganisation
from apps.governance.phoenix_operations import CONFIG_MODELS, CONFIG_FIELDS
from apps.governance.phoenix_rules import ACTIONS, proposed_circuit


class CompositionField(forms.Field):
    """Composition saisie par fonctions, en conservant les autres éléments du référentiel."""
    widget = forms.Textarea

    def __init__(self, *args, current=None, **kwargs):
        self.current = deepcopy(current or {})
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, dict):
            counts = value.get('effectifs') or {}
            return '\n'.join(f'{role} : {counts[role]}' if isinstance(counts, dict) and role in counts else role
                             for role in value.get('categories', []))
        return value

    def to_python(self, value):
        if isinstance(value, dict):
            return value
        text = (value or '').strip()
        if text.startswith('{'):
            try:
                parsed = json.loads(text)
            except ValueError:
                raise forms.ValidationError('La composition doit contenir une fonction par ligne.')
            if isinstance(parsed, dict):
                return parsed
        result = deepcopy(self.current)
        roles, counts = [], {}
        for line in text.splitlines():
            role, separator, count = line.strip().rpartition(':')
            if separator:
                if not count.strip().isdigit() or not role.strip():
                    raise forms.ValidationError('Renseigner un effectif entier positif ou nul après les deux-points.')
                role = role.strip()
                counts[role] = int(count.strip())
            else:
                role = line.strip()
            if role and role not in roles:
                roles.append(role)
        result['categories'] = roles
        result['effectifs'] = counts or None
        return result


def configuration_form(kind, version, data=None, instance=None):
    form_class = forms.modelform_factory(CONFIG_MODELS[kind], fields=CONFIG_FIELDS[kind])
    form = form_class(data, instance=instance)
    if kind == 'poste':
        if not instance:
            form.fields.pop('display_created_at')
            form.fields.pop('display_updated_at')
        else:
            for name in ('display_created_at', 'display_updated_at'):
                field = form.fields[name]
                field.widget = forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'phoenix-input'})
                field.input_formats = ['%Y-%m-%dT%H:%M']
                field.help_text = 'L’horodatage système d’origine reste conservé. Laisser vide pour l’afficher.'
            form.fields['audit_date_reason'] = forms.CharField(
                required=False, max_length=500, label='Motif de correction des dates',
                help_text='Obligatoire si une date affichée change ; la correction est enregistrée au journal.',
                widget=forms.Textarea(attrs={'rows': 2, 'class': 'phoenix-input'}),
            )
    if kind == 'organe':
        form.fields['composition'] = CompositionField(
            label='Fonctions et effectifs', required=False, current=instance.composition if instance else {},
            help_text='Une fonction par ligne. Ajouter « : nombre » pour préciser l’effectif.',
        )
    organs = version.organes.all()
    sc = organs.filter(type='SC')
    mandates = MandatOrganisation.objects.filter(Q(poste__organe__version=version) | Q(groupe__sc__version=version))
    options = {'organe': organs, 'parent': organs.exclude(pk=instance.pk) if instance and kind == 'organe' else organs, 'sc': sc, 'perimeter': organs, 'poste': PosteOrganisation.objects.filter(organe__version=version),
               'groupe': GroupeCible.objects.filter(sc__version=version), 'gt': GroupeCible.objects.filter(sc__version=version),
               'mandat': mandates, 'expert': Expert.objects.filter(status='ACTIVE', user__is_active=True).select_related('user'),
               'delegated_from': HabilitationAction.objects.filter(mandat__in=mandates, delegated_from__isnull=True),
               'norme': Norme.all_objects.all()}
    empty_labels = {'organe': 'Sélectionner un organe', 'parent': 'Aucun organe de rattachement',
                    'required_structure': 'Aucune structure requise', 'poste': 'Aucun poste',
                    'groupe': 'Aucun groupe de travail', 'gt': 'Aucun groupe de travail',
                    'sc': 'Sélectionner une sous-commission', 'delegated_from': 'Aucune délégation',
                    'expert': 'Sélectionner un titulaire', 'mandat': 'Sélectionner un mandat',
                    'norme': 'Sélectionner une norme', 'perimeter': 'Sélectionner un périmètre'}
    for name, field in form.fields.items():
        if name in options:
            field.queryset = options[name]
        field.widget.attrs['class'] = 'phoenix-input'
        if hasattr(field, 'empty_label') and name in empty_labels:
            field.empty_label = empty_labels[name]
        if isinstance(field, forms.DateField) and not isinstance(field, forms.DateTimeField):
            field.widget = forms.DateInput(attrs={'type': 'date', 'class': 'phoenix-input'})
            field.input_formats = ['%Y-%m-%d']
    if 'action' in form.fields:
        form.fields['action'] = forms.ChoiceField(choices=list(ACTIONS.items()), widget=forms.Select(attrs={'class': 'phoenix-input'}))
    if kind == 'circuit' and not instance:
        form.initial['configuration'] = proposed_circuit()
        form.initial['code'] = 'phoenix-v1'
        form.initial['name'] = 'Circuit CNE-ITP — proposition à confirmer'
    # Les FK versionnées sont fixées côté serveur avant le clean du ModelForm.
    if kind in ('organe', 'circuit', 'rattachement'):
        form.instance.version = version
    labels = {'code': 'Code', 'name': 'Intitulé', 'official_name': 'Dénomination confirmée', 'status': 'Statut',
              'type': 'Type d’organe', 'parent': 'Organe de rattachement', 'domain': 'Périmètre de compétence',
              'composition': 'Fonctions et effectifs', 'source_document': 'Document de référence',
              'source_reference': 'Source et référence de décision', 'origin_label': 'Origine institutionnelle',
              'title': 'Fonction confirmée', 'category': 'Catégorie', 'required_structure': 'Structure requise',
              'display_created_at': 'Date de création affichée', 'display_updated_at': 'Date de modification affichée',
              'appointment_reference': 'Acte de nomination', 'start_date': 'Début', 'end_date': 'Fin',
              'decision_reference': 'Référence de décision', 'enabled': 'Habilitation en vigueur', 'perimeter': 'Périmètre',
              'delegated_from': 'Habilitation source de la délégation', 'configuration': 'États, transitions et conditions approuvés',
              'effective_from': 'Prise d’effet', 'effective_to': 'Fin de rattachement', 'function': 'Fonction du mandat'}
    labels['capacity'] = 'Qualité au titre de laquelle la personne agit'
    for name, label in labels.items():
        if name in form.fields:
            form.fields[name].label = label
    return form


class DossierCreateForm(forms.Form):
    mandate = forms.ModelChoiceField(queryset=MandatOrganisation.objects.none(), label='Mandat sélectionné')
    circuit = forms.ModelChoiceField(queryset=CircuitOrganisation.objects.none(), label='Circuit approuvé')
    gt = forms.ModelChoiceField(queryset=GroupeCible.objects.none(), label='GT confirmé')
    reference_number = forms.CharField(max_length=50, label='Référence')
    title = forms.CharField(max_length=500, label='Titre')
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Description')
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 12}), label='Première version')

    def __init__(self, *args, user, version, **kwargs):
        from apps.governance.phoenix_services import has_organisation_action
        from apps.governance.phoenix_workflow import mandates_for
        super().__init__(*args, **kwargs)
        mandates = mandates_for(user)
        groups = list(GroupeCible.objects.filter(sc__version=version, status__in=['VALIDATED', 'ACTIVE']))
        identifiers = [group.pk for group in groups if any(has_organisation_action(user, mandate, 'document.creer', groupe=group) for mandate in mandates)]
        self.fields['mandate'].queryset = mandates
        self.fields['gt'].queryset = GroupeCible.objects.filter(pk__in=identifiers)
        self.fields['circuit'].queryset = version.circuits.filter(status='VALIDATED', decision_reference=version.circuit_reference)
        self.fields['mandate'].empty_label = 'Sélectionner un mandat'
        self.fields['gt'].empty_label = 'Sélectionner un groupe de travail'
        self.fields['circuit'].empty_label = 'Sélectionner un circuit approuvé'
        for field in self.fields.values():
            field.widget.attrs['class'] = 'phoenix-input'


class ActivationForm(forms.Form):
    activation_reference = forms.CharField(max_length=250, label='Décision de mise en service')
    gt_catalogue_reference = forms.CharField(max_length=250, label='Catalogue GT approuvé')
    permissions_reference = forms.CharField(max_length=250, label='Matrice des pouvoirs approuvée')
    circuit_reference = forms.CharField(max_length=250, label='Circuit approuvé')


class DecisionForm(forms.Form):
    mandate = forms.ModelChoiceField(queryset=MandatOrganisation.objects.none(), label='Mandat sélectionné')
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    transition = forms.CharField(max_length=60, widget=forms.HiddenInput)
    request_key = forms.CharField(max_length=100, widget=forms.HiddenInput)
    decision_reference = forms.CharField(max_length=250, label='Référence de la décision')
    reason = forms.CharField(widget=forms.Textarea, label='Motif et conclusion')
