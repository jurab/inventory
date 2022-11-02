
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Order, OrderPart
from modules.models import Device, Module
from parts.models import Part


class OrderPartInlineAdmin(admin.TabularInline):

    model = OrderPart
    extra = 1
    fields = 'part', 'count', 'price', 'stock', 'demand', 'ordered', 'missing', 'supplier'
    autocomplete_fields = 'part',
    readonly_fields = 'stock', 'demand', 'ordered', 'missing'
    ordering = 'part__name',

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        self.part_values_dict = {item['id']: item for item in Part.annotate_missing().values('id', 'total_demand', 'total_ordered', 'missing')}
        return qs

    def _get_value(self, order_part, field):
        return self.part_values_dict[order_part.part.id][field]

    def stock(self, order_part):
        return order_part.part.stock

    def demand(self, order_part):
        return self._get_value(order_part, 'total_demand')

    def ordered(self, order_part):
        return self._get_value(order_part, 'total_ordered')

    def missing(self, order_part):
        return self._get_value(order_part, 'missing')


class OrderForm(forms.ModelForm):

    all_missing_parts = forms.BooleanField(required=False)
    device = forms.ModelChoiceField(queryset=Device.objects.all(), required=False)
    device_count = forms.IntegerField(initial=1)
    module = forms.ModelChoiceField(queryset=Module.objects.all(), required=False)
    module_count = forms.IntegerField(initial=1)

    def save(self, *args, **kwargs):
        order = super().save(*args, **kwargs)

        if not order.id or not order.parts.exists():
            all_missing_parts = self.data.get('all_missing_parts', None)
            device_id = self.data.get('device', None)
            device_count = int(self.data.get('device_count', None))
            module_id = self.data.get('module', None)
            module_count = int(self.data.get('module_count', None))

            if len([i for i in (all_missing_parts, module_id) if i]) > 1:
                raise ValidationError("You can only choose one option from all_missing_parts/device/module.")

            if all_missing_parts:
                name = 'All Missing Parts'
                parts_args = {}
            elif device_id:
                name = Device.objects.get(id=device_id).name
                parts_args = {'device_id': device_id, 'multiplier': device_count}
            elif module_id:
                name = Module.objects.get(id=module_id).name
                parts_args = {'module_id': module_id, 'multiplier': module_count}
            else:
                return

            order.name = f"{name} {Order.objects.filter(name__icontains=name).count() + 1}"
            order.save()
            order.populate_parts(**parts_args)

        return order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = '__str__', 'pk', 'delivered', 'part_count', 'price', 'created', 'modified'

    fieldsets = (
        ("", {"fields": (
            ('pk'),
            ('name'),
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

    def part_count(self, order):
        return int(order.parts.count())

    def price(self, order):
        price = order.price()
        return '$' + str(price) if price else None
