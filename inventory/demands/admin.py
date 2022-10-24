
from django.contrib import admin

from .models import ModuleDemand


@admin.register(ModuleDemand)
class ModuleDemandAdmin(admin.ModelAdmin):
    list_display = 'module_name', 'count',
    list_editable = 'count',

    search_fields = 'module__name',
    readonly_fields = 'created', 'modified', 'module_name'
