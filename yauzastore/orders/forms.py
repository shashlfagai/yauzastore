from django import forms
from .models import OrderItem, Order
from shop.models import ProductSize
import requests


class UpdateCartForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['quantity', 'size']

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super(UpdateCartForm, self).__init__(*args, **kwargs)
        if product:
            self.fields['size'].queryset = (
                ProductSize.objects
                .filter(product=product)
            )
        else:
            self.fields['size'].queryset = ProductSize.objects.none()


class OrderHistoryForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'status',
            'delivery_address',
            'payment_status',
            'delivery_status'
        ]


class PromoCodeForm(forms.Form):
    code = forms.CharField(
        label="Промокод",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите промокод'
            }
        )
    )


class RegionChoiceForm(forms.Form):
    region = forms.ChoiceField(label='Выберите регион')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_regions()

    def fetch_regions(self):
        # URL API
        url = "https://api.edu.cdek.ru/v2/location/regions"
        params = {
            'country_codes': 'RU',  # Выбор страны (например, Россия)
            'size': 100,  # Количество регионов
            'page': 0,     # Номер страницы
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            regions = response.json()
            # Заполняем поле выбора региона
            choices = [
                (
                    region['region_code'],
                    region['region']
                ) for region in regions
            ]
            self.fields['region'].choices = choices
        else:
            self.fields['region'].choices = [
                ("0", "Не удалось загрузить регионы")
            ]
