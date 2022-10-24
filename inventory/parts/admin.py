
from django.contrib import admin
from django.db.models import F

from .models import Part
from core.utils import custom_titled_filter
from demands.models import ModuleDemand


class StockFilter(admin.SimpleListFilter):
    title = ('availability')
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return (
            ('below_demand', 'Below Demand'),
            ('in_stock', 'In Stock'),
            ('ordered', 'Ordered'),
        )

    def queryset(self, request, queryset):
        option = self.value()

        if not option:
            return queryset

        return {
            'below_demand': self.below_demand,
            'in_stock': self.in_stock,
            'ordered': self.ordered,
        }[option](queryset)

    def below_demand(self, queryset):
        return queryset.filter(total_demand__gt=F('stock'))

    def in_stock(self, queryset):
        pass

    def ordered(self, queryset):
        pass


class ModulePartInline(admin.TabularInline):
    model = Part.modules.through
    extra = 1
    fields = 'module_name', 'count'
    readonly_fields = 'module_name',
    autocomplete_fields = 'module',
    ordering = 'module__name',


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = 'uuid', 'name', 'stock', 'demand', 'min_price', 'current_price', 'category', 'title', 'description', 'tme_type', 'farnell_code', 'comp_value', 'comp_class'
    list_editable = 'name', 'stock', 'min_price', 'current_price', 'category', 'title', 'description', 'tme_type', 'farnell_code', 'comp_value', 'comp_class'

    list_filter = 'category', StockFilter, ('modules__name', custom_titled_filter('module name'))
    search_fields = 'uuid', 'name'
    readonly_fields = 'created', 'modified'

    inlines = ModulePartInline,

    def get_queryset(self, request):
        return ModuleDemand.parts()

    def demand(self, part):
        return part.total_demand
