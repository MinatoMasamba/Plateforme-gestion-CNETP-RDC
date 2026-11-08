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
    class Meta:
        model = AppVersion
        fields = (
            'version_number', 'channel', 'release_notes', 'known_issues',
            'min_os_version', 'compatibility_notes', 'status',
        )
        widgets = {
            'version_number': SoftTextInput(),
            'channel': SoftSelect(),
            'release_notes': SoftTextarea(attrs={'rows': 8}),
            'known_issues': SoftTextarea(),
            'min_os_version': SoftTextInput(),
            'compatibility_notes': SoftTextarea(),
            'status': SoftSelect(),
        }


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
