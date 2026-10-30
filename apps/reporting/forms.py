from django import forms

from apps.governance.models import GroupeCible, Organe
from apps.norms.models import Norme

from .catalog import TYPES
from .models import FinancialLine, Report, ReportEvidence, ReportTypePermission
from .services import active_version, reporting_mandates


class ReportForm(forms.ModelForm):
    report_type = forms.ChoiceField(choices=[(code, f'{code} · {title}') for code, (_, title, _) in TYPES.items()], label='Modèle de rapport')

    class Meta:
        model = Report
        fields = ('report_type', 'title', 'pole', 'norme', 'sc', 'gt', 'period_start', 'period_end', 'recipient')
        labels = {'title': 'Titre du rapport', 'pole': 'Pôle concerné', 'norme': 'Norme concernée', 'sc': 'Sous-commission', 'gt': 'Groupe de travail', 'period_start': 'Début de la période', 'period_end': 'Fin de la période', 'recipient': 'Destinataire prévu'}
        widgets = {'period_start': forms.DateInput(attrs={'type': 'date'}), 'period_end': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        version = active_version()
        if version and not self.instance.version_id:
            self.instance.version = version
        mandates = reporting_mandates(user, 'rapport.rediger', version)
        permitted_types = set(ReportTypePermission.objects.filter(
            habilitation__mandat__in=mandates, habilitation__action='rapport.rediger',
            enabled=True,
        ).values_list('report_type', flat=True))
        self.fields['report_type'].choices = [
            (code, f'{code} · {title}') for code, (_, title, _) in TYPES.items() if code in permitted_types
        ]
        pole_ids = set()
        central = False
        for mandate in mandates.prefetch_related('habilitations'):
            for grant in mandate.habilitations.filter(action='rapport.rediger', enabled=True):
                if grant.perimeter.type == 'ST':
                    central = True
                elif grant.perimeter.type == 'ST_POLE':
                    pole_ids.add(grant.perimeter_id)
        poles = Organe.objects.filter(version=version, type='ST_POLE') if version else Organe.objects.none()
        self.fields['pole'].queryset = poles if central else poles.filter(pk__in=pole_ids)
        self.fields['sc'].queryset = Organe.objects.filter(version=version, type='SC') if version else Organe.objects.none()
        self.fields['gt'].queryset = GroupeCible.objects.filter(sc__version=version) if version else GroupeCible.objects.none()
        self.fields['norme'].queryset = Norme.all_objects.all().order_by('reference_number')
        for field in self.fields.values():
            field.widget.attrs['class'] = 'report-input'

    def clean(self):
        cleaned = super().clean()
        sc, gt = cleaned.get('sc'), cleaned.get('gt')
        if sc and gt and gt.sc_id != sc.pk:
            self.add_error('gt', 'Ce GT ne relève pas de la sous-commission choisie.')
        if cleaned.get('period_start') and cleaned.get('period_end') and cleaned['period_end'] < cleaned['period_start']:
            self.add_error('period_end', 'La fin doit suivre le début.')
        return cleaned


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = ReportEvidence
        fields = ('title', 'source_reference', 'file')
        labels = {'title': 'Intitulé de la pièce', 'source_reference': 'Référence vérifiable', 'file': 'Fichier justificatif'}

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError('Fichier de 20 Mo maximum.')
            if file.name.rsplit('.', 1)[-1].lower() not in {'pdf', 'doc', 'docx', 'xlsx', 'png', 'jpg', 'jpeg'}:
                raise forms.ValidationError('Format admis : PDF, Word, Excel, PNG ou JPEG.')
        return file


class FinancialLineForm(forms.ModelForm):
    class Meta:
        model = FinancialLine
        fields = ('norme', 'task', 'activity', 'need', 'result_expected', 'quantity', 'unit', 'unit_cost', 'currency', 'confirmed_funding', 'committed', 'liquidated', 'ordered', 'paid', 'evidence')
        labels = {'activity': 'Activité', 'need': 'Besoin justifié', 'result_expected': 'Livrable attendu', 'quantity': 'Quantité', 'unit': 'Unité', 'unit_cost': 'Coût unitaire', 'currency': 'Devise', 'confirmed_funding': 'Financement confirmé', 'committed': 'Engagé', 'liquidated': 'Liquidé', 'ordered': 'Ordonnancé', 'paid': 'Payé', 'evidence': 'Pièce justificative'}

    def __init__(self, *args, report, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['norme'].queryset = Norme.all_objects.all()
        self.fields['evidence'].queryset = report.evidence.all()
        for name in ('confirmed_funding', 'committed', 'liquidated', 'ordered', 'paid'):
            self.fields[name].widget.attrs['min'] = '0'

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('norme') and not cleaned.get('task'):
            self.add_error('norme', 'Lier la ligne à une norme ou une tâche.')
        for name in ('confirmed_funding', 'committed', 'liquidated', 'ordered', 'paid'):
            if cleaned.get(name) is not None and cleaned[name] < 0:
                self.add_error(name, 'Le montant ne peut pas être négatif.')
        return cleaned
