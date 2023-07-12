from django import forms
from .models import Rental


class RentalForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Rental
        fields = ['client', 'car', 'start_date', 'end_date']
        labels = {
            'client': 'Клиент',
            'car': 'Техника',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
        }
