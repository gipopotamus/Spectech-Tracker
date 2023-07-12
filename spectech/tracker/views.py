from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from django.views.generic import DetailView
from django_redis import get_redis_connection
from .models import Rental, Car
from .forms import RentalForm
import json


def rental_calendar(request):
    today = timezone.now().date()
    dates = [(today + timedelta(days=i)).strftime('%m-%d') for i in range(31)]

    redis_conn = get_redis_connection()
    calendar = redis_conn.get('rental_calendar')

    if calendar:
        booked_dates = json.loads(calendar)
    else:
        rentals = Rental.objects.all()
        booked_dates = {}
        cars = Car.objects.all()

        for car in cars:
            booked_dates[car.name] = []

        for rental in rentals:
            car_name = rental.car.name
            rental_data = {
                rental.id: [date.strftime('%m-%d') for date in
                            (rental.start_date + timedelta(days=i) for i in
                             range((rental.end_date - rental.start_date).days + 1))]
            }
            booked_dates[car_name].append(rental_data)

        redis_conn.set('rental_calendar', json.dumps(booked_dates), ex=86400)

    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('rental_calendar'))
    else:
        form = RentalForm()

    context = {
        'dates': dates,
        'booked_dates': booked_dates,
        'form': form,
    }

    return render(request, 'rental_calendar.html', context)


class RentalDetailView(DetailView):
    model = Rental
    template_name = 'rental_detail.html'
    context_object_name = 'rental'
