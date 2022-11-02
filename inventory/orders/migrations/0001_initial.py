# Generated by Django 3.2.9 on 2022-11-02 14:39

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('suppliers', '0001_initial'),
        ('parts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(blank=True, max_length=256, unique=True)),
                ('delivered', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField(default=1)),
                ('price', models.FloatField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_parts', to='orders.order')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_parts', to='parts.part')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='suppliers.supplier')),
            ],
            options={
                'unique_together': {('order', 'part')},
            },
        ),
        migrations.AddField(
            model_name='order',
            name='parts',
            field=models.ManyToManyField(related_name='orders', through='orders.OrderPart', to='parts.Part'),
        ),
    ]
