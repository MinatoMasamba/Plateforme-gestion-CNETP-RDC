from django import forms

from .models import PublicAmendement

_INPUT_CLASSES = "w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200"


class PublicAmendementSubmissionForm(forms.ModelForm):
    class Meta:
        model = PublicAmendement
        fields = [
            'proposed_by_name', 'proposed_by_email', 'proposed_by_organization',
            'proposed_by_province', 'title', 'description', 'justification',
        ]
        widgets = {
            'proposed_by_name': forms.TextInput(attrs={'placeholder': 'Nom complet', 'class': _INPUT_CLASSES}),
            'proposed_by_email': forms.EmailInput(attrs={'placeholder': 'Adresse email', 'class': _INPUT_CLASSES}),
            'proposed_by_organization': forms.TextInput(attrs={'placeholder': 'Organisation (optionnel)', 'class': _INPUT_CLASSES}),
            'proposed_by_province': forms.TextInput(attrs={'placeholder': 'Province (optionnel)', 'class': _INPUT_CLASSES}),
            'title': forms.TextInput(attrs={'placeholder': "Titre de l'amendement", 'class': _INPUT_CLASSES}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Description détaillée', 'class': _INPUT_CLASSES}),
            'justification': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Justification (optionnel)', 'class': _INPUT_CLASSES}),
        }
