# Generated by Django 3.2.15 on 2022-10-09 07:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CachedAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.TextField(db_index=True, unique=True, verbose_name='Адрес')),
                ('lng', models.DecimalField(blank=True, decimal_places=14, max_digits=17, null=True, validators=[django.core.validators.MinValueValidator(-180.0), django.core.validators.MaxValueValidator(180.0)], verbose_name='Долгота')),
                ('lat', models.DecimalField(blank=True, decimal_places=14, max_digits=16, null=True, validators=[django.core.validators.MinValueValidator(-90.0), django.core.validators.MaxValueValidator(90.0)], verbose_name='Широта')),
                ('last_update', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Дата обновления')),
                ('valid', models.BooleanField(default=False, verbose_name='Адрес корректен?')),
            ],
        ),
    ]
