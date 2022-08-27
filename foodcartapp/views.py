from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    errors = validate_order_body(request.data)

    if errors:
        return Response(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    order = save_user_order(request.data)
    return Response({'order_num': order.pk})


@transaction.atomic
def save_user_order(order_body):
    order = Order.objects.create(
        first_name=order_body['firstname'],
        last_name=order_body['lastname'],
        phone_number=order_body['phonenumber'],
        address=order_body['address'],
    )

    for product in order_body.get('products'):
        order.products.create(product_id=product['product'], quantity=product['quantity'])

    return order


def validate_order_body(order_body: dict):
    errors = defaultdict(list)

    # check required nonempty string
    required_str_keys = ['firstname', 'lastname', 'phonenumber', 'address']
    for str_key in required_str_keys:
        try:
            if not isinstance(order_body[str_key], str):
                errors[str_key].append(f'{str_key} must be a string')
            elif not len(order_body[str_key]):
                errors[str_key].append(f'{str_key} must be a nonempty string')
        except KeyError as missing_key:
            errors[str_key].append(f'{missing_key} not found')

    # validate phone number
    if 'phonenumber' not in errors:
        try:
            validate_international_phonenumber(order_body['phonenumber'])
        except ValidationError as e:
            errors['phonenumber'].append(e)

    if 'products' not in order_body.keys():
        errors['products'].append('products not found')

    # validate products content
    if not isinstance(order_body.get('products'), list):
        errors['products'].append('products must be a list')
    elif not len(order_body['products']):
        errors['products'].append('products cannot be empty')
    else:
        if any(key not in product for key in ['product', 'quantity'] for product in order_body['products']):
            errors['products'].append(f'Incorrect product was found in cart')

        product_ids = {product.get('product') for product in order_body['products']}
        not_founded = product_ids - set(Product.objects.filter(pk__in=product_ids).values_list('pk', flat=True))
        if not_founded:
            errors['products'].append(f'This is incorrect products: {not_founded}')

        quantities = [product.get('quantity') for product in order_body['products']]
        if any(not isinstance(quantity, int) or quantity <= 0 for quantity in quantities):
            errors['products'].append(f'Incorrect quantity was found')

    return errors
