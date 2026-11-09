from django import forms

from .models import (
    AppAnnouncement,
    AppCategory,
    AppReleaseFile,
    AppScreenshot,
    AppVersion,
    SoftwareApp,
)


class SoftTextInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'appstore-input')
        super().__init__(*args, **kwargs)


class SoftTextarea(forms.Textarea):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'appstore-input')
        attrs.setdefault('rows', 4)
        super().__init__(*args, **kwargs)


class SoftSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'appstore-input')
        super().__init__(*args, **kwargs)


class SoftFileInput(forms.ClearableFileInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('class', 'appstore-file')
        super().__init__(*args, **kwargs)


class AppCategoryForm(forms.ModelForm):
    class Meta:
        model = AppCategory
        fields = ('name', 'slug', 'description', 'sort_order', 'is_active')
        widgets = {
            'name': SoftTextInput(),
            'slug': SoftTextInput(),
            'description': SoftTextarea(),
            'sort_order': SoftTextInput(attrs={'type': 'number', 'min': 0}),
        }


class SoftwareAppForm(forms.ModelForm):
    class Meta:
        model = SoftwareApp
        fields = (
            'name', 'slug', 'short_description', 'full_description', 'features',
            'publisher', 'category', 'icon', 'is_featured', 'is_published',
        )
        widgets = {
            'name': SoftTextInput(),
            'slug': SoftTextInput(),
            'short_description': SoftTextInput(),
            'full_description': SoftTextarea(attrs={'rows': 8}),
            'features': SoftTextarea(attrs={'rows': 6}),
            'publisher': SoftTextInput(),
            'category': SoftSelect(),
            'icon': SoftFileInput(),
        }


class AppVersionForm(forms.ModelForm):
    MODE_AUTO = 'auto'
    MODE_MANUAL = 'manual'
    MODE_CHOICES = (
        (MODE_AUTO, 'Auto-incrémentation'),
        (MODE_MANUAL, 'Choisir manuellement (ex. 1.3.0-beta)'),
    )

    version_mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        initial=MODE_AUTO,
        widget=SoftSelect(),
        label='Numérotation',
        help_text='Par défaut la version suivante est calculée automatiquement. Choisissez le mode manuel pour un numéro libre (bêta, hotfix, etc.).',
    )

    class Meta:
        model = AppVersion
        fields = (
            'version_number', 'channel', 'release_notes', 'known_issues',
            'min_os_version', 'compatibility_notes', 'status',
        )
        widgets = {
            'version_number': SoftTextInput(attrs={
                'placeholder': 'ex. 1.3.0-beta',
            }),
            'channel': SoftSelect(),
            'release_notes': SoftTextarea(attrs={'rows': 8}),
            'known_issues': SoftTextarea(),
            'min_os_version': SoftTextInput(),
            'compatibility_notes': SoftTextarea(),
            'status': SoftSelect(),
        }

    def __init__(self, *args, application=None, suggested_version='', **kwargs):
        self.application = application
        self.suggested_version = suggested_version or '1.0.0'
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance') or getattr(self, 'instance', None)
        is_edit = bool(instance and instance.pk)

        if is_edit:
            self.fields['version_mode'].initial = self.MODE_MANUAL
            self.fields['version_mode'].widget = forms.HiddenInput()
            self.fields['version_number'].required = True
            self.fields['version_number'].help_text = 'Modification du numéro existant.'
        else:
            self.fields['version_number'].required = False
            self.fields['version_number'].initial = ''
            self.fields['version_number'].help_text = (
                f'Si auto : {self.suggested_version}. '
                'Sinon saisissez un numéro personnalisé.'
            )
            if not self.data:
                self.fields['version_mode'].initial = self.MODE_AUTO

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('version_mode') or self.MODE_AUTO
        number = (cleaned.get('version_number') or '').strip()
        instance = getattr(self, 'instance', None)
        is_edit = bool(instance and instance.pk)

        if is_edit:
            if not number:
                self.add_error('version_number', 'Le numéro de version est obligatoire.')
            cleaned['version_number'] = number
            return cleaned

        if mode == self.MODE_MANUAL:
            if not number:
                self.add_error(
                    'version_number',
                    'Indiquez un numéro de version (ex. 1.3.0-beta) en mode manuel.',
                )
            cleaned['version_number'] = number
        else:
            cleaned['version_number'] = self.suggested_version
            cleaned['version_mode'] = self.MODE_AUTO
        return cleaned


class AppReleaseFileForm(forms.ModelForm):
    package = forms.FileField(
        required=False,
        widget=SoftFileInput(),
        label='Fichier à distribuer',
    )
    approve_now = forms.BooleanField(
        required=False,
        initial=True,
        label='Approuver immédiatement (sortie de quarantaine)',
    )

    class Meta:
        model = AppReleaseFile
        fields = ('platform', 'architecture', 'install_notes')
        widgets = {
            'platform': SoftSelect(),
            'architecture': SoftSelect(),
            'install_notes': SoftTextarea(),
        }


class AppScreenshotForm(forms.ModelForm):
    class Meta:
        model = AppScreenshot
        fields = ('image', 'caption', 'sort_order')
        widgets = {
            'image': SoftFileInput(),
            'caption': SoftTextInput(),
            'sort_order': SoftTextInput(attrs={'type': 'number', 'min': 0}),
        }


class AppAnnouncementForm(forms.ModelForm):
    class Meta:
        model = AppAnnouncement
        fields = (
            'title', 'body', 'kind', 'image', 'application', 'version',
            'is_pinned', 'status',
        )
        widgets = {
            'title': SoftTextInput(),
            'body': SoftTextarea(attrs={'rows': 8}),
            'kind': SoftSelect(),
            'image': SoftFileInput(),
            'application': SoftSelect(),
            'version': SoftSelect(),
            'status': SoftSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['version'].queryset = AppVersion.objects.select_related('application').all()
        self.fields['application'].queryset = SoftwareApp.objects.all()
