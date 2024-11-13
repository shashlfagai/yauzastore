from django import forms
from .models import ProductSize


class AddToCartForm(forms.Form):
    size = forms.ModelChoiceField(
        queryset=ProductSize.objects.none(),
        label='',
        empty_label='Размер'
    )

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        if product:
            available_sizes = ProductSize.objects.filter(
                product=product,
                quantity__gt=0
            )
            self.fields['size'].queryset = available_sizes

            if available_sizes.count() == 1:
                self.fields['size'].initial = available_sizes.first()

        self.fields['size'].widget.attrs.update({
            'class': "form-select form-select-sm text-center",
            'aria-label': "Small select example"
        })
