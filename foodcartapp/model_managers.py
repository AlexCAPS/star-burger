from django.db import models
from django.db.models import F, Sum


class OrderCostManager(models.Manager):
    def with_cost(self):
        return self.annotate(
            cost=Sum(F('products__frozen_price') * F('products__quantity'))
        )
