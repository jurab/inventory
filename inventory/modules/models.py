

from django.db import models
from django.db.models import Sum, F
from core.models import TimestampModel
from core.utils import round_or_none
from parts.models import Part


class Module(TimestampModel):

    name = models.CharField(max_length=256, unique=True)
    parts = models.ManyToManyField(Part, through='ModulePart', related_name='modules')

    class Meta:
        ordering = 'name',

    def __repr__(self):
        return f"<Module {self.id}: {self.name}>"

    def __str__(self):
        return self.name

    def price(self, price_field):
        price_field = f"part__{price_field}"
        return ModulePart.objects.filter(module=self).aggregate(total=Sum(F('count') * F(price_field)))['total']

    @property
    def min_price(self):
        return round_or_none(self.price('min_price'), 2)

    @property
    def current_price(self):
        return round_or_none(self.price('current_price'), 2)


class ModulePart(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='module_parts')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='module_parts')
    count = models.IntegerField(default=1)

    class Meta:
        ordering = 'module__name', 'part__name'

    def __repr__(self):
        return f"<ModulePart {self.id}: {self.module.name} - {self.part.name} x {self.count}>"

    def __str__(self):
        return self.__repr__()

    @property
    def min_price(self):
        return round_or_none(self.part.min_price, 2)

    @property
    def current_price(self):
        return round_or_none(self.part.current_price, 2)

    @property
    def module_name(self):
        return self.module.name


class Device(models.Model):
    name = models.CharField(max_length=256)
    modules = models.ManyToManyField(Module, through='DeviceModule', related_name='devices')

    class Meta:
        ordering = 'name',

    def __repr__(self):
        return f"<Device {self.id}: {self.name}>"

    def __str__(self):
        return self.name


class DeviceModule(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='device_modules')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='device_modules')
    count = models.IntegerField(default=1)

    class Meta:
        unique_together = 'module', 'device'

    def __repr__(self):
        return f"<DeviceModule {self.id}: {self.device.name} - {self.module.name} x {self.count}>"

    def __str__(self):
        return self.__repr__()

    @property
    def device_name(self):
        return self.device.name
