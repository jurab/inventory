

from random import randint

from django.core.management.base import BaseCommand
from django.db import transaction

from parts.models import Part, PartOption


CATS = [
    'condensers',
    'diodes',
    'connectors',
    'inductors',
    'transistors',
    'resistors',
    'trimmers',
    'integrated-resonators',
    'misc'
]


class Command(BaseCommand):

    def handle(self, *args, **options):

        with transaction.atomic():
            data = [row.split('\t') for row in open('inventory/parts.tsv', 'r')]
            data = [[item.strip() or None for item in row] for row in data]

            parts = []
            category = data[0][0]

            for i, row in enumerate(data, 1):

                if row[0] in CATS:
                    category = row[0]
                else:
                    row = row + [None] * (7 - len(row))  # normalize row
                    try:
                        uuid, name, title, desc, tme_type, farnell_code, comp_value = row
                    except ValueError as e:
                        print(f'Invalid row #{i}\n{type(e)}: {e}\n{row}')
                        return

                    parts.append(Part(
                        uuid=uuid,
                        name=name,
                        category=category,
                        title=title,
                        description=desc,
                        tme_type=tme_type,
                        farnell_code=farnell_code,
                        comp_value=comp_value,
                        stock=randint(0, 10000),
                        min_price=randint(0, 200) / 100
                    ))

            Part.objects.bulk_create(parts)

            part_options = []

            for part in Part.objects.all():
                option_names = [item.strip() for item in part.name.split('/')]
                for name in option_names:
                    part_options.append(PartOption(name=name, part_id=part.pk))

            PartOption.objects.bulk_create(part_options)
