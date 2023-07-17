import json
from datetime import timedelta

from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView
from django_redis import get_redis_connection
from .forms import RentalForm
from .models import Car, Rental


from datetime import timedelta


class RentalCalendarView(View):
    template_name = 'rental_calendar.html'

    def get_context_data(self):
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

                shifts_data = []
                for shift in rental.shifts.all():
                    shift_dates = [date.strftime('%m-%d') for date in
                                   (shift.start_date + timedelta(days=i) for i in
                                    range((shift.end_date - shift.start_date).days + 1))]
                    shifts_data.append({
                        'worker': shift.worker.full_name,
                        'dates': shift_dates,
                        'total_salary': float(shift.total_salary()),
                    })

                rental_data['shifts'] = shifts_data
                booked_dates[car_name].append(rental_data)

            redis_conn.set('rental_calendar', json.dumps(booked_dates), ex=86400)

        return {
            'dates': dates,
            'booked_dates': booked_dates,
            'form': RentalForm(),
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        print(context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save()
            return redirect('rental_calendar')
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class RentalDeleteView(View):
    def post(self, request, *args, **kwargs):
        rental_id = self.kwargs['pk']
        try:
            rental = Rental.objects.get(id=rental_id)
            rental.delete()
            data = {
                'status': 'success',
                'message': 'Rental deleted successfully.',
            }
        except Rental.DoesNotExist:
            data = {
                'status': 'error',
                'message': 'Rental not found.',
            }

        return JsonResponse(data)


class RentalDetailView(DetailView):
    model = Rental
    template_name = 'rental_detail.html'
    context_object_name = 'rental'


class CarListView(ListView):
    model = Car
    template_name = 'lists/cars.html'

    def get_queryset(self):
        sort = self.request.GET.get('sort')
        if sort:
            return Car.objects.order_by(sort)
        else:
            return Car.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cars = context['object_list']
        for car in cars:
            car.url = reverse('car_detail', args=[car.pk])
        return context


class CarDetailView(DetailView):
    model = Car
    template_name = 'lists/car_detail.html'
    context_object_name = 'car'


class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('rental_calendar')  # Замените 'car_list' на URL вашей страницы после успешного входа

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)