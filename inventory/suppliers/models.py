
from django.db import models

from core.models import TimestampModel
from parts.models import Part


class Supplier(models.Model):

    name = models.CharField(max_length=256, unique=True)
    parts = models.ManyToManyField(Part, through='PartPrice', related_name='suppliers')


class PartPrice(TimestampModel):

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='prices')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='prices')
    price = models.IntegerField()
