from django import forms
from django.forms import formset_factory
from .models import Rental, Shift


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['worker', 'fuel_filled', 'fuel_consumed', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class RentalForm(forms.ModelForm):
    shifts = formset_factory(ShiftForm, extra=1)

    class Meta:
        model = Rental
        fields = ['client', 'car', 'start_date', 'end_date']
        labels = {
            'client': 'Клиент',
            'car': 'Техника',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
