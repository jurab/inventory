# Generated by Django 3.2.9 on 2022-10-24 14:11

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('parts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ModulePart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(default=1)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_parts', to='modules.module')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_parts', to='parts.part')),
            ],
            options={
                'ordering': ('module__name', 'part__name'),
            },
        ),
        migrations.AddField(
            model_name='module',
            name='parts',
            field=models.ManyToManyField(related_name='modules', through='modules.ModulePart', to='parts.Part'),
        ),
        migrations.CreateModel(
            name='DeviceModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(default=1)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_modules', to='modules.device')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_modules', to='modules.module')),
            ],
        ),
        migrations.AddField(
            model_name='device',
            name='modules',
            field=models.ManyToManyField(related_name='devices', through='modules.DeviceModule', to='modules.Module'),
        ),
    ]
