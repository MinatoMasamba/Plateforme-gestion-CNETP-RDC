from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet, construct_instance

from .models import CTCMembership


class CTCMembershipInlineFormSet(BaseInlineFormSet):
    """Empêche de recréer une adhésion CTC (même ctc + expert), y compris
    lorsqu'une adhésion désactivée existe déjà (unique_together l'interdit)."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        parent_expert = self.instance if self.fk.name == 'expert' else None
        parent_ctc = self.instance if self.fk.name == 'ctc' else None
        seen = set()

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            expert = form.cleaned_data.get('expert') or parent_expert
            ctc = form.cleaned_data.get('ctc') or parent_ctc
            if not expert or not ctc:
                continue

            key = (ctc.pk, expert.pk)
            if key in seen:
                raise ValidationError(
                    "Cet expert est déjà rattaché à cette cellule dans ce formulaire."
                )
            seen.add(key)

            existing = CTCMembership.all_objects.filter(ctc=ctc, expert=expert)
            if form.instance.pk:
                existing = existing.exclude(pk=form.instance.pk)
            duplicate = existing.first()
            if not duplicate:
                continue
            if duplicate.is_active:
                raise ValidationError(
                    "Une adhésion CTC existe déjà pour cet expert. "
                    "Modifiez-la au lieu d'en créer une nouvelle."
                )
            # Adhésion désactivée : on la réactive immédiatement au lieu de
            # créer un doublon interdit par unique_together.
            construct_instance(form, duplicate, form._meta.fields, form._meta.exclude)
            duplicate.is_active = True
            form.instance = duplicate
