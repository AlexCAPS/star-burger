from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint, Q, F, CheckConstraint, Count, Value
from phonenumber_field.modelfields import PhoneNumberField

from foodcartapp.model_managers import OrderCostManager


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'N', 'Новый'
        ASSEMBLY = 'A', 'Передан ресторану'
        IN_DELIVERY = 'D', 'Передан курьеру'
        FINISHED = 'F', 'Завершён'
        CANCELED = 'C', 'Отменён'

    class PaymentMethod(models.TextChoices):
        EMPTY = '', 'Не выбран'
        CASH = 'CASH', 'Наличный расчёт'
        CARD_ON_SITE = 'SITE', 'Картой на сайте'
        CARD_TO_COURIER = 'CARD', 'Картой курьеру'

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=128,
        db_index=True,
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=128,
        db_index=True,
    )

    phone_number = PhoneNumberField(
        verbose_name='Телефон',
        db_index=True,
    )

    address = models.TextField(
        verbose_name='Адрес',
        blank=False,
    )

    created_at = models.DateTimeField(
        verbose_name='Время заказа',
        auto_now_add=True,
        db_index=True,
    )

    called_at = models.DateTimeField(
        verbose_name='Время звонка',
        null=True, blank=True,
        db_index=True,
    )

    delivered_at = models.DateTimeField(
        verbose_name='Время доставки',
        null=True, blank=True,
        db_index=True,
    )

    status = models.CharField(
        verbose_name='Статус',
        max_length=1,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True
    )

    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
    )

    payment_method = models.CharField(
        verbose_name='Способ оплаты',
        max_length=4,
        choices=PaymentMethod.choices,
        blank=True,
        default=PaymentMethod.EMPTY,
        db_index=True,
    )

    selected_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Выбранный ресторан',
        related_name='orders',
        null=True, blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    objects = OrderCostManager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

        constraints = [
            CheckConstraint(
                check=Q(called_at__gte=F('created_at')) | Q(called_at__isnull=True),
                name='call_after_create',
            ),
            CheckConstraint(
                check=Q(delivered_at__gte=F('called_at')) | Q(called_at__isnull=True) | Q(delivered_at__isnull=True),
                name='delivered_after_call',
            ),
        ]

    def get_appropriate_restaurants(self):
        """

        :return: Return queryset of restaurants which can create full order
        """
        products = self.products.all().values_list('product', flat=True)

        appropriate_restaurants = (
            Restaurant.objects.filter(
                menu_items__product__in=products,
                menu_items__availability=True,
            ).annotate(
                req_prod_count=Count('pk'),
            ).filter(
                req_prod_count=products.count()
            )
        )
        return appropriate_restaurants

    @staticmethod
    def get_many_orders_appropriate_restaurants(orders):
        """
        Selects for the list of orders restaurants that can prepare the order.

        :param orders: QuerySet of orders for which will found appropriated restaurants
        :return: QuerySet of appropriated restaurants with annotated order_pk - primary key of associated order
        """
        # products_count need for grouped and select appropriated restaurants
        orders = orders.select_related().annotate(products_count=Count('products'))

        restaurants_queries = [
            (
                Restaurant.objects.filter(
                    menu_items__product__in=order.products.values_list('product', flat=True),
                    menu_items__availability=True,
                ).annotate(
                    order_pk=Value(order.pk),
                    req_prod_count=Count('pk'),
                ).filter(
                    order_pk=Value(order.pk),
                    req_prod_count=order.products_count
                )
            )
            for order in orders
        ]

        appropriate_restaurants_qs = Restaurant.objects.none()
        appropriate_restaurants_qs = appropriate_restaurants_qs.union(*restaurants_queries, all=True)
        return appropriate_restaurants_qs

    def __str__(self):
        return f'{self.first_name} {self.phone_number} (Заказ № {self.pk} от {self.created_at} {self.status})'


class ProductOrderQuantity(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='продукт',
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='заказ',
    )

    frozen_price = models.DecimalField(
        verbose_name='цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    quantity = models.PositiveSmallIntegerField(
        verbose_name='количество',
    )

    class Meta:
        verbose_name = 'продукты в заказе'
        verbose_name_plural = 'продукты в заказах'

        constraints = [
            UniqueConstraint(
                name='UniqueProductInOrder',
                fields=('product', 'order'),
            )
        ]

    def __str__(self):
        return f'{self.product} {self.quantity} шт. (Заказ № {self.order.pk})'
