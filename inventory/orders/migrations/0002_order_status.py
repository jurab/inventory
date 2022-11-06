# Generated by Django 3.2.9 on 2022-11-06 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('ordered', 'Ordered'), ('delivered', 'Delivered')], default='pending', max_length=64),
        ),
    ]
