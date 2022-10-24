

from django.core.management.base import BaseCommand
from django.db import transaction

from modules.models import Module, ModulePart
from parts.models import Part


class Command(BaseCommand):

    def handle(self, *args, **options):

        with transaction.atomic():
            data = [row.split('\t') for row in open('inventory/modules.tsv', 'r')]
            data = [[item.strip() or None for item in row] for row in data]

            header = data[0]
            data = data[2:]

            for name in header:
                Module.objects.create(name=name)

            module_parts = []
            module_name_id_dict = {name: pk for pk, name in Module.objects.values_list('id', 'name')}
            part_uuid_id_dict = {uuid: pk for pk, uuid in Part.objects.values_list('id', 'uuid')}

            for i, row in enumerate(data):
                try:

                    uuid, counts = int(row[0]), row[10:] + [None] * (len(header) - len(row[1:]))
                    counts = [int(count.split(',')[0]) if count else None for count in counts]

                    if not any(counts): continue
                    part_pk = part_uuid_id_dict.pop(uuid)
                    # print([f"{header}: {uuid} x {count}" for header, count in zip(header, counts) if count])
                    for count, name in zip(counts, header):
                        if count:
                            # print(i, uuid, name, count)
                            module_parts.append(ModulePart(part_id=part_pk, module_id=module_name_id_dict[name], count=count))

                except Exception as e:
                    print(f'Invalid row #{i}\n{type(e)}: {e}\n{part_pk}:{counts}')
                    raise e

            ModulePart.objects.bulk_create(module_parts)
