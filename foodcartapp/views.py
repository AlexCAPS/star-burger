from collections import defaultdict

from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
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

    required_str_keys = ['firstname', 'lastname', 'phonenumber', 'address']
    for str_key in required_str_keys:
        try:
            if not isinstance(order_body[str_key], str):
                errors[str_key].append(f'{str_key} must be a string')
        except KeyError as missing_key:
            errors[str_key].append(f'{missing_key} not found')

    if 'products' not in order_body.keys():
        errors['products'].append('products not found')

    if not isinstance(order_body.get('products'), list):
        errors['products'].append('products must be list')
    else:
        if not len(order_body['products']):
            errors['products'] = ['products cannot be empty']

    return errors
