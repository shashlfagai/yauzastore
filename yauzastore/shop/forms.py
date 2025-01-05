from django import forms
from .models import ProductSize, PartnerProjects

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


class RealizationForm(forms.ModelForm):
    agree_to_privacy_policy = forms.BooleanField(
        required=True,
        label="Я согласен на обработку персональных данных"
    )
    class Meta:
        model = PartnerProjects
        fields = [
            'first_name',
            'phone',
            'contact_preference',
            'project_name',
            'product_description',
            'product_link',
            'social_link',
            'additional_info',
            'agree_to_privacy_policy'
        ]
        widgets = {
            'contact_preference': forms.Select(),
            'product_description': forms.Textarea(attrs={'rows': 4}),
        }


class RentalForm(forms.ModelForm):
    agree_to_privacy_policy = forms.BooleanField(
        required=True,
        label="Я согласен на обработку персональных данных"
    )
    class Meta:
        model = PartnerProjects
        fields = [
            'first_name',
            'phone',
            'contact_preference',
            'project_name',
            'product_description',
            'product_link',
            'social_link',
            'additional_info',
            'shelf_preference',
            'agree_to_privacy_policy'
        ]
        widgets = {
            'contact_preference': forms.Select(),
            'shelf_preference': forms.Select(),
            'product_description': forms.Textarea(attrs={'rows': 4}),
        }

class OtherForm(forms.ModelForm):
    agree_to_privacy_policy = forms.BooleanField(
        required=True,
        label="Я согласен на обработку персональных данных"
    )
    class Meta:
        model = PartnerProjects
        fields = [
            'first_name',
            'phone',
            'contact_preference',
            'social_link',
            'additional_info',
            'agree_to_privacy_policy'
        ]
        widgets = {
            'contact_preference': forms.Select(),
            'shelf_preference': forms.Select(),
            'product_description': forms.Textarea(attrs={'rows': 4}),
        }
