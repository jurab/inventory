
from django.contrib import admin

from .models import Module, ModulePart, Device, DeviceModule
from core.utils import custom_titled_filter


class ModulePartInlineAdmin(admin.TabularInline):
    model = ModulePart
    extra = 1
    fields = 'part', 'count', 'min_price', 'current_price'
    readonly_fields = 'min_price', 'current_price'
    autocomplete_fields = 'part',
    ordering = 'part__name',


class DeviceModuleInline(admin.TabularInline):
    model = Device.modules.through
    extra = 1
    fields = 'device_name', 'count'
    readonly_fields = 'device_name',
    autocomplete_fields = 'device',
    ordering = 'device__name',


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = 'name', 'min_price', 'current_price'
    fields = 'name', 'created', 'modified',  # 'min_price', 'current_price'
    readonly_fields = 'created', 'modified'  # , 'min_price', 'current_price'
    list_editable = ()

    search_fields = 'name',
    list_filter = ('devices__name', custom_titled_filter('device name')),

    inlines = ModulePartInlineAdmin, DeviceModuleInline

    save_as = True


class DeviceModuleInlineAdmin(admin.TabularInline):
    model = DeviceModule
    extra = 1


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    fields = 'name',
    inlines = DeviceModuleInlineAdmin,
    search_fields = 'name',
