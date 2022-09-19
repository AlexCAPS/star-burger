from django import forms
from django.core.exceptions import ValidationError

from foodcartapp.models import Order


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def clean_called_at(self):
        cleaned_called_at = self.cleaned_data.get('called_at')

        if cleaned_called_at is None:
            return

        if cleaned_called_at < self.instance.created_at:
            raise ValidationError('Звонок не может быть совершён до создания заказа')

        return cleaned_called_at

    def clean_delivered_at(self):
        cleaned_delivered_at = self.cleaned_data.get('delivered_at')

        if cleaned_delivered_at is None:
            return

        called_at = self.cleaned_data.get('called_at')

        if called_at is None:
            raise ValidationError('Доставка не может быть совершена без звонка оператора')

        if cleaned_delivered_at < called_at:
            raise ValidationError('Доставка не может быть совершена до звонка оператора')

        return cleaned_delivered_at
