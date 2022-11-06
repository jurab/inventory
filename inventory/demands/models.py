

from django.db import models
from django.db.models import F, Value, Sum

from core.models import TimestampModel
from utils.core import group_by
from utils.django import dictionary_annotation, has_annotation
from modules.models import Module, ModulePart
from parts.models import Part


class ModuleDemand(TimestampModel):

    module = models.ForeignKey(Module, on_delete=models.PROTECT, related_name='demands')
    count = models.IntegerField(default=1)
    completed_count = models.IntegerField(default=0)

    def __repr__(self):
        return f"<ModuleDemand {self.id}: {self.module.name} x {self.count}>"

    def __str__(self):
        return self.__repr__()

    def missing_module_parts(self):
        return self.module.module_parts.annotate(missing_count=Value(self.count) * F('count') - F('part__stock')).filter(missing_count__gt=0)

    def set_completed(self, count=None):
        module_parts = self.module_parts.all()

        count = count or self.count
        parts_to_update = []

        for module_part in module_parts:
            part = module_part.part
            part.stock -= module_part.count * count
            parts_to_update.append(part)

        Part.bulk_update(parts_to_update)
        self.completed_count += count
        self.save()

    def min_price(self):
        return self.module.min_price() * self.count()

    @property
    def completed(self):
        return self.count == self.completed_count

    @property
    def module_name(self):
        return self.module.name

    @classmethod
    def annotate_parts(cls, qs=None):

        if qs and has_annotation(qs, 'total_demand'): return qs

        module_parts = ModulePart.objects.select_related('module').exclude(module__demands=None)
        module_parts = module_parts.annotate(total_demand=Sum('module__demands__count') * F('count'))
        module_parts_by_uuid = group_by(module_parts, 'part.uuid')
        uuid_demand_dict = {uuid: sum([module_part.total_demand for module_part in module_parts]) for uuid, module_parts in module_parts_by_uuid.items()}

        # TODO case annotation will be slow for large parts querysets
        parts = dictionary_annotation(
            qs=qs or Part.objects.all(),
            key_column_name='uuid',
            new_column_name='total_demand',
            field_type=models.IntegerField,
            data_dict=uuid_demand_dict,
            default=0
        )

        return parts
