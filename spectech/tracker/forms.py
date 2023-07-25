from django import forms
from django.forms import formset_factory
from django.utils import timezone

from .models import Rental, Shift


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ('worker', 'date', 'start_time', 'end_time', 'fuel_filled', 'fuel_consumed')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().strftime('%Y-%m-%d')}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.rental:
            rental = instance.rental
            self.fields['date'].widget.attrs['min'] = rental.start_date.strftime('%Y-%m-%d')
            self.fields['date'].widget.attrs['max'] = rental.end_date.strftime('%Y-%m-%d')


class RentalForm(forms.ModelForm):
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
            'start_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
        }
