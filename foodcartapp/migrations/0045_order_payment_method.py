# Generated by Django 3.2.15 on 2022-09-19 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0044_auto_20220916_1846'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('', 'Не выбран'), ('CASH', 'Наличный расчёт'), ('SITE', 'Картой на сайте'), ('CARD', 'Картой курьеру')], db_index=True, default='', max_length=4, verbose_name='Способ оплаты'),
        ),
    ]
