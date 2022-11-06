
from django.contrib import admin
from django.db.models import F

from .models import Part
from core.utils import custom_titled_filter
from orders.models import Order


class StockFilter(admin.SimpleListFilter):
    title = ('availability')
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'In Stock'),
            ('insuficient_stock', 'Insuficient Stock'),
            ('ordered', 'Ordered'),
            ('missing', 'Missing'),
        )

    def queryset(self, request, queryset):
        option = self.value()

        if not option:
            return queryset

        return {
            'insuficient_stock': self.insuficient_stock,
            'in_stock': self.in_stock,
            'ordered': self.ordered,
            'missing': self.missing,
        }[option](queryset)

    def insuficient_stock(self, queryset):
        return queryset.filter(total_demand__gt=F('stock'))

    def in_stock(self, queryset):
        return queryset.filter(stock__gt=0)

    def ordered(self, queryset):
        return queryset.filter(total_ordered__gt=0)

    def missing(self, queryset):
        return queryset.filter(missing__gt=0)


class ModulePartInline(admin.TabularInline):
    model = Part.modules.through
    extra = 1
    fields = 'module_name', 'count'
    readonly_fields = 'module_name',
    autocomplete_fields = 'module',
    ordering = 'module__name',


@admin.action(description='Order Missing')
def create_order(modeladmin, request, queryset):
    order = Order.objects.create()
    queryset = queryset.annotate(to_order=F('total_demand') - F('total_ordered') - F('stock'))
    queryset = queryset.filter(to_order__gt=0)
    order.bulk_add_parts(*zip(*queryset.values_list('id', 'to_order')))


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = 'uuid', 'name', 'stock', 'demand', 'ordered', 'missing', 'avg_price', 'min_price', 'current_price', 'category', 'title', 'description', 'tme_type', 'farnell_code', 'comp_value', 'comp_class'
    list_editable = 'name', 'stock', 'min_price', 'current_price', 'category', 'title', 'description', 'tme_type', 'farnell_code', 'comp_value', 'comp_class'

    list_filter = 'category', StockFilter, ('modules__name', custom_titled_filter('module name'))
    search_fields = 'uuid', 'name'
    readonly_fields = 'created', 'modified'

    inlines = ModulePartInline,
    actions = create_order,

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return Part.annotate_missing(qs)

    def demand(self, part):
        return part.total_demand

    def ordered(self, part):
        return part.total_ordered

    def missing(self, part):
        return part.missing

    def avg_price(self, part):
        return part.avg_price
