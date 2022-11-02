

from django.db import models
from core.models import TimestampModel
from core.utils import names_enum


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


class PartOption(TimestampModel):
    name = models.CharField(max_length=256)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
