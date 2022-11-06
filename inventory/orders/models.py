
import hashlib

from django.db import models
from django.db.models import F, Sum, Avg

from core.models import TimestampModel
from core.utils import group_by, dictionary_annotation, has_annotation, names_enum, annotate_related_aggregate
from demands.models import ModuleDemand
from modules.models import ModulePart, Device
from parts.models import Part
from suppliers.models import Supplier


STATUS_CHOICES = names_enum(
    'pending',
    'ordered',
    'delivered'
)


class Order(TimestampModel):

    name = models.CharField(max_length=256, unique=True, blank=True)
    parts = models.ManyToManyField(Part, related_name='orders', through='OrderPart')
    status = models.CharField(max_length=64, choices=STATUS_CHOICES, default='pending')

    def __repr__(self):
        return f"<Order {self.id}: {self.name}>"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        h = int(hashlib.sha1(str(self.created).encode("utf-8")).hexdigest(), 16) % (10 ** 8)
        self.name = self.name or f"Parts Order {h}"
        return super().save(*args, **kwargs)

    def price(self):
        order_parts = OrderPart.objects.filter(order_id=self.id).annotate(total_price=F('price') * F('count'))
        price = order_parts.aggregate(Sum('total_price'))['total_price__sum']
        return round(float(price), 2) if price else None

    def set_delivered(self, model_part_dict=None):

        parts_to_update = []
        order_parts = OrderPart.objects.filter(order=self)

        for order_part in order_parts:
            part = order_part.part
            part.stock += order_part.count

        Part.bulk_update(parts_to_update)
        self.status = 'delivered'

    def bulk_add_parts(self, part_ids, counts, count_multiplier=1):

        to_create = []

        for part_id, count in zip(part_ids, counts):
            to_create.append(OrderPart(
                order=self,
                part_id=part_id,
                count=count * count_multiplier,
            ))

        OrderPart.objects.bulk_create(to_create)

    def populate_parts(self, module_id=None, device_id=None, part_ids=None, multiplier=1):

        if sum([bool(arg) for arg in (module_id, device_id, part_ids)]) > 1:
            raise ValueError("`populate_parts` received more than one source argument.")

        if module_id:
            part_ids, counts = zip(*ModulePart.objects.filter(module_id=module_id).values_list('part_id', 'count').exclude(module__demands=None))
            count_multiplier = multiplier

        elif device_id:
            part_ids, counts = zip(*Device.objects.get(id=device_id).part_id_counts().items())
            count_multiplier = multiplier

        elif part_ids:
            counts = [1] * len(part_ids)

        else:
            part_ids, counts = zip(*ModuleDemand.parts().exclude(total_demand__isnull=True).values_list('id', 'total_demand'))
            count_multiplier = multiplier

        self.bulk_add_parts(part_ids, counts, count_multiplier)

    @classmethod
    def annotate_parts(cls, qs=None):

        if qs and has_annotation(qs, 'total_ordered'): return qs

        order_parts_by_uuid = group_by(OrderPart.objects.annotate(part_uuid=F('part__uuid')), 'part_uuid')
        # TODO next line should be optimized with Aggregate / SQL `GROUP BY`
        uuid_ordered_dict = {uuid: sum([order_part.count for order_part in order_parts]) for uuid, order_parts in order_parts_by_uuid.items()}

        # TODO case annotation will be slow for large parts querysets
        parts = dictionary_annotation(
            qs=qs or Part.objects.all(),
            key_column_name='uuid',
            new_column_name='total_ordered',
            field_type=models.IntegerField,
            data_dict=uuid_ordered_dict,
            default=0
        )

        return parts


class OrderPart(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_parts')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='order_parts')
    count = models.PositiveIntegerField(default=1)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    price = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = 'order', 'part'

    def __repr__(self):
        return f"<OrderPart {self.id}: {self.part.name} x {self.count}>"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def annotate_parts(cls, qs=None):
        if qs and has_annotation(qs, 'avg_price'): return qs
        return annotate_related_aggregate(
            qs,
            field='avg_price',
            related_field='part',
            related_attribute='price',
            RelatedModel=OrderPart,
            function='Avg'
        )
