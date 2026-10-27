"""Formulaires génériques et formulaires utilisateur de la console."""
from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.db import models
from django.forms import modelform_factory

from apps.core.models import User

from .console_registry import model_admin_fields


USER_FIELDS = (
    'username',
    'first_name',
    'last_name',
    'email',
    'phone',
    'province',
    'is_active',
    'is_expert',
    'is_ctc_staff',
    'is_minister',
    'is_staff',
    'is_superuser',
)


class ConsoleUserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = USER_FIELDS

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not actor or not actor.is_superuser:
            self.fields.pop('is_superuser', None)
            self.fields.pop('is_staff', None)

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.is_superuser:
            user.is_staff = True
        if commit:
            user.save()
        return user


class ConsoleUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = USER_FIELDS

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not actor or not actor.is_superuser:
            self.fields.pop('is_superuser', None)
            self.fields.pop('is_staff', None)

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.is_superuser:
            user.is_staff = True
        if commit:
            user.save()
        return user


def _widget_for_field(field):
    if isinstance(field, models.JSONField):
        return forms.Textarea(attrs={'rows': 8})
    if isinstance(field, models.TextField):
        return forms.Textarea(attrs={'rows': 6})
    if isinstance(field, models.DateTimeField):
        return forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        )
    if isinstance(field, models.DateField):
        return forms.DateInput(attrs={'type': 'date'})
    if isinstance(field, models.TimeField):
        return forms.TimeInput(attrs={'type': 'time'})
    if isinstance(field, models.ManyToManyField):
        return forms.SelectMultiple(attrs={'size': 8})
    if isinstance(field, models.ForeignKey):
        return forms.Select()
    return None


def build_model_form(model_admin, request, obj=None):
    model = model_admin.model
    fields = model_admin_fields(model_admin, request, obj)
    model_fields = {
        field.name: field
        for field in model._meta.get_fields()
        if field.name in fields
    }
    widgets = {}
    for name, field in model_fields.items():
        widget = _widget_for_field(field)
        if widget is not None:
            widgets[name] = widget

    form_class = modelform_factory(model, fields=fields, widgets=widgets)
    form_class.__name__ = f'Console{model.__name__}Form'
    return form_class
