

from django.db import models
from django.utils import timezone
from graphene.types.datetime import DateTime


class TimestampModel(models.Model):
    """An abstract base class model providing self-updating created and modified fields."""

    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    class TypeMeta:
        extra_fields = (
            ('created', DateTime),
            ('modified', DateTime),
        )


class S3Object(models.Model):

    s3url = models.CharField(max_length=1023)

    class Meta:
        abstract = True
