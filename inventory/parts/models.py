

from django.db import models
from django.db.models import F, Case, When
from core.models import TimestampModel
from core.utils import names_enum, has_annotation


PART_CATEGORIES = names_enum(
    'condensers',
    'diodes',
    'connectors',
    'inductors',
    'transistors',
    'resistors',
    'trimmers',
    'integrated-resonators',
    'misc'
)


class Part(TimestampModel):

    uuid = models.IntegerField(unique=True)
    name = models.CharField(max_length=256, unique=True)
    category = models.CharField(max_length=256, choices=PART_CATEGORIES)
    title = models.CharField(max_length=512, null=True)
    description = models.CharField(max_length=512, null=True)

    tme_type = models.CharField(max_length=512, null=True)
    farnell_code = models.CharField(max_length=512, null=True)
    comp_value = models.CharField(max_length=512, null=True)
    comp_class = models.CharField(max_length=512, null=True)

    stock = models.BigIntegerField(default=0)
    min_price = models.FloatField(default=0)
    current_price = models.FloatField(default=0)

    class Meta:
        ordering = 'uuid',

    def __repr__(self):
        return f"<Part {self.id}: {self.uuid}: {self.name}>"

    def __str__(self):
        return self.name

    @classmethod
    def annotate_missing(self, qs=None):
        if qs and has_annotation(qs, 'missing'): return qs

        from demands.models import ModuleDemand
        from orders.models import Order

        qs = ModuleDemand.annotate_parts(qs)
        qs = Order.annotate_parts(qs)
        qs = qs.annotate(_missing=F('total_demand') - F('total_ordered') - F('stock'))
        qs = qs.annotate(
            missing=Case(
                When(_missing__gte=0, then=F('_missing')),
                default=0
            )
        )

        return qs


class PartOption(TimestampModel):
    name = models.CharField(max_length=256)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
