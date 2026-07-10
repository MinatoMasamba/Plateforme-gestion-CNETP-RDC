from django.contrib import admin
from .models import Draft


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ('id', 'ctm', 'wg', 'type', 'domain', 'created_at')
    search_fields = ('ctm', 'wg', 'type', 'domain')
