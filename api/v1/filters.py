from django_filters.rest_framework import FilterSet, CharFilter, BooleanFilter
from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG


class UserFilter(FilterSet):
    """Filtres pour les utilisateurs"""
    username = CharFilter(field_name='username', lookup_expr='icontains')
    email = CharFilter(field_name='email', lookup_expr='icontains')
    is_expert = BooleanFilter(field_name='is_expert')
    is_ctc_staff = BooleanFilter(field_name='is_ctc_staff')
    is_minister = BooleanFilter(field_name='is_minister')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'is_expert', 'is_ctc_staff', 'is_minister']


class ExpertFilter(FilterSet):
    """Filtres pour les experts"""
    status = CharFilter(field_name='status', lookup_expr='exact')
    structure = CharFilter(field_name='structure__name', lookup_expr='icontains')
    
    class Meta:
        model = Expert
        fields = ['status', 'structure', 'ctm_choices__id']


class StructureFilter(FilterSet):
    """Filtres pour les structures"""
    category = CharFilter(field_name='category', lookup_expr='exact')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    
    class Meta:
        model = Structure
        fields = ['category', 'name']


class CTMFilter(FilterSet):
    """Filtres pour les CTM"""
    name = CharFilter(field_name='name', lookup_expr='icontains')
    number = CharFilter(field_name='number', lookup_expr='exact')
    
    class Meta:
        model = CTM
        fields = ['name', 'number']


class WGFilter(FilterSet):
    """Filtres pour les WG"""
    name = CharFilter(field_name='name', lookup_expr='icontains')
    ctm = CharFilter(field_name='ctm__number', lookup_expr='exact')
    
    class Meta:
        model = WG
        fields = ['name', 'ctm']
