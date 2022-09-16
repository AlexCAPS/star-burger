from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html

from .models import Product, Order, ProductOrderQuantity
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)

    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url,
                           src=obj.image.url)

    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductOrderQuantity)
class ProductOrderQuantityAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', ]
    search_fields = ['order', 'product', ]


class ProductOrderQuantityInline(admin.TabularInline):
    model = ProductOrderQuantity
    extra = 0
    readonly_fields = ['frozen_price']

    def get_fields(self, request, obj=None):
        fields_for_create = ['product', 'order', 'quantity']
        fields_for_update = fields_for_create + self.readonly_fields
        return fields_for_update if obj else fields_for_create


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'status', 'first_name', 'last_name', 'phone_number', 'created_at', 'view_cost']
    search_fields = list_display
    list_filter = ['created_at', 'status']
    inlines = [
        ProductOrderQuantityInline,
    ]

    readonly_fields = ['view_cost']

    def get_queryset(self, request):
        return Order.objects.with_cost()

    @admin.display(description='цена', ordering='cost')
    def view_cost(self, order):
        return order.cost

    def save_formset(self, request, form, formset, change):
        """
        Update frozen_price in form like actual product price
        :param request:
        :param form:
        :param formset:
        :param change:
        :return:
        """
        product_order_quantities: list = formset.save(commit=False)
        for product_order_quantity in product_order_quantities:
            product_order_quantity.frozen_price = product_order_quantity.product.price
        formset.save()

    def response_post_save_change(self, request, obj):
        if "next" in request.GET:
            # add redirect to url from "next" param if it will be required
            return HttpResponseRedirect(reverse('restaurateur:view_orders'))

        response = super(OrderAdmin, self).response_post_save_change(request, obj)
        return response
