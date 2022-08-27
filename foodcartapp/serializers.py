from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField, ListField
from rest_framework.serializers import Serializer

from foodcartapp.models import Product


class ProductSerializer(Serializer):
    product = IntegerField()
    quantity = IntegerField(min_value=1)

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')


class OrderSerializer(Serializer):
    firstname = CharField()
    lastname = CharField()
    phonenumber = PhoneNumberField()
    address = CharField()
    products = ListField(
        child=ProductSerializer(),
        allow_empty=False,
    )

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    @staticmethod
    def validate_products(products):
        product_ids = {product['product'] for product in products}
        not_founded = product_ids - set(Product.objects.filter(pk__in=product_ids).values_list('pk', flat=True))

        if not_founded:
            raise ValidationError(f'This is incorrect products: {not_founded}')

        return products
