
from django.db import models
from core.models import TimestampModel
from parts.models import Part
from suppliers.models import Supplier


class Order(TimestampModel):

    name = models.CharField(max_length=256, unique=True, blank=True)
    parts = models.ManyToManyField(Part, related_name='orders', through='OrderPart')
    delivered = models.BooleanField(default=False)

    def set_delivered(self, model_part_dict=None):

        parts_to_update = []
        order_parts = OrderPart.objects.filter(order=self)

        for order_part in order_parts:
            part = order_part.part
            part.stock += order_part.count

        Part.bulk_update(parts_to_update)

    def bulk_add_parts(self, part_ids, counts, count_multiplier=1):

        to_create = []

        for part_id, count in zip(part_ids, counts):
            print(part_id, count)
            to_create.append(OrderPart(
                order=self,
                part_id=part_id,
                count=count * count_multiplier,
            ))
            print(to_create[-1].count)

        OrderPart.objects.bulk_create(to_create)


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
