from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class CachedAddress(models.Model):
    address = models.TextField(
        verbose_name='Адрес',
        blank=False,
        db_index=True,
        unique=True,
    )

    lng = models.DecimalField(
        verbose_name='Долгота',
        max_digits=17,
        decimal_places=14,
        validators=[
            MinValueValidator(-180.0),
            MaxValueValidator(180.0),
        ],
        null=True, blank=True,
    )

    lat = models.DecimalField(
        verbose_name='Широта',
        max_digits=16,
        decimal_places=14,
        validators=[
            MinValueValidator(-90.0),
            MaxValueValidator(90.0),
        ],
        null=True, blank=True,
    )

    last_update = models.DateTimeField(
        verbose_name='Дата обновления',
        auto_now=True,
        db_index=True,
    )

    valid = models.BooleanField(
        verbose_name='Адрес корректен?',
        default=False,
    )

    def __str__(self):
        return self.address
