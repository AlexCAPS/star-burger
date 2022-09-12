from copy import deepcopy

from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField, ListField
from rest_framework.serializers import Serializer

from foodcartapp.models import Product, Order


class ProductSerializer(Serializer):
    product = IntegerField()
    quantity = IntegerField(min_value=1)

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')


class OrderSerializer(Serializer):
    firstname = CharField(source='first_name')
    lastname = CharField(source='last_name')
    phonenumber = PhoneNumberField(source='phone_number')
    address = CharField()
    products = ListField(
        child=ProductSerializer(),
        allow_empty=False,
        write_only=True,
    )

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    @transaction.atomic
    def create(self, validated_order_data):
        validated_order_data = deepcopy(validated_order_data)

        incoming_products = validated_order_data.pop('products')

        order = Order.objects.create(**validated_order_data)

        product_ids = {product['product'] for product in incoming_products}
        used_products = Product.objects.filter(pk__in=product_ids).values('pk', 'price')
        product_price_map = {obj['pk']: obj['price'] for obj in used_products}

        for product in incoming_products:
            product_id = product['product']
            order.products.create(
                product_id=product_id,
                quantity=product['quantity'],
                frozen_price=product_price_map[product_id],
            )

        return order

    @staticmethod
    def validate_products(products):
        product_ids = {product['product'] for product in products}
        not_founded = product_ids - set(Product.objects.filter(pk__in=product_ids).values_list('pk', flat=True))

        if not_founded:
            raise ValidationError(f'This is incorrect products: {not_founded}')

        return products
