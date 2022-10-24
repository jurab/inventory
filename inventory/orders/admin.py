
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Order, OrderPart
from demands.models import ModuleDemand
from modules.models import Device, Module, ModulePart


class OrderPartInlineAdmin(admin.TabularInline):
    model = OrderPart
    extra = 1
    fields = 'part', 'count', 'price', 'supplier'
    autocomplete_fields = 'part',
    ordering = 'part__name',


class OrderForm(forms.ModelForm):
    all_missing_parts = forms.BooleanField(required=False)
    device = forms.ModelChoiceField(queryset=Device.objects.all(), required=False)
    device_count = forms.IntegerField(initial=1)
    module = forms.ModelChoiceField(queryset=Module.objects.all(), required=False)
    module_count = forms.IntegerField(initial=1)

    def save(self, *args, **kwargs):
        order = super().save(*args, **kwargs)

        all_missing_parts = self.data.get('all_missing_parts', None)
        # device_id = self.data.get('device', None)
        # device_count = self.data.get('device_count', None)
        module_id = self.data.get('module', None)
        module_count = self.data.get('module_count', None)

        if len([i for i in (all_missing_parts, module_id) if i]) > 1:
            raise ValidationError("You can only choose one option from all_missing_parts/device/module.")

        if all_missing_parts:
            order.bulk_add_parts(*zip(*ModuleDemand.parts().exclude(total_demand__isnull=True).values_list('id', 'total_demand')), module_count)
        elif module_id:
            data = ModulePart.objects.filter(module_id=module_id).values_list('part_id', 'count').exclude(module__demands=None)
            order.bulk_add_parts(*zip(*data), module_count)

        return order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = 'pk', 'delivered'

    fieldsets = (
        ("", {"fields": (
            ('pk'),
            ('delivered',),
        )}),
        ("Info", {"fields": (
            ('created',),
            ('modified',),
        )}),
        ("Create Options", {"fields": (
            ('all_missing_parts',),
            ('device_count', 'device'),
            ('module_count', 'module'),
        )}),
    )

    readonly_fields = 'pk', 'created', 'modified'
    list_editable = 'delivered',
    search_fields = 'parts__name',
    inlines = OrderPartInlineAdmin,

    form = OrderForm

    save_as = True
