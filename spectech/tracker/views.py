import json
from django.db import models
from django.contrib.auth.views import LoginView
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import ExtractHour
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.views import View
from django.views.generic import DetailView, ListView, CreateView
from django_redis import get_redis_connection
from .forms import RentalForm, ShiftForm
from .models import Car, Rental, Shift, Client

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
                    rental.id: [rental.client.name, [date.strftime('%m-%d') for date in
                                (rental.start_date + timedelta(days=i) for i in
                                 range((rental.end_date - rental.start_date).days + 1))]]
                }

                booked_dates[car_name].append(rental_data)

            redis_conn.set('rental_calendar', json.dumps(booked_dates), ex=86400)

        return {
            'dates': dates,
            'booked_dates': booked_dates,
            'form': RentalForm(),
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rental = self.get_object()

        # Рассчитываем общую оплату за каждую смену
        shifts = rental.shifts.annotate(
            total_hours=ExpressionWrapper(
                ExtractHour(F('end_time') - F('start_time')),
                output_field=FloatField()  # Используем FloatField для временной разницы
            ),
            total_payment=ExpressionWrapper(
                ExtractHour(F('end_time') - F('start_time')) * F('worker__hourly_rate'),
                output_field=FloatField()  # Используем FloatField для оплаты смены
            )
        )

        # Рассчитываем общую сумму оплаты за все смены
        total_salary = shifts.aggregate(total_salary=Sum('total_payment'))['total_salary'] or 0
        context['shift_form'] = ShiftForm(initial={'rental' : self.object.pk})
        context['shifts'] = shifts
        context['total_salary'] = total_salary

        return context

    def form_valid(self, form):
        shift_form = ShiftForm(self.request.POST)
        if shift_form.is_valid():
            shift_form.save()
        return redirect('rental_info', pk=self.object.pk)


class RentalListView(ListView):
    model = Rental
    template_name = 'lists/rentals.html'
    context_object_name = 'rentals'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = timezone.now().date()
        context['active_rentals'] = Rental.objects.filter(start_date__lte=current_date, end_date__gte=current_date)
        context['upcoming_rentals'] = Rental.objects.filter(start_date__gt=current_date)
        context['archive_rentals'] = Rental.objects.filter(end_date__lt=current_date)
        return context


class ShiftCreateView(CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'rental_detail.html'  # Шаблон такой же, как у RentalDetailView

    def get_success_url(self):
        # Получаем значение 'pk' из параметров запроса и используем его в URL-адресе
        pk = self.kwargs['pk']
        return reverse_lazy('rental_detail', kwargs={'pk': pk})

    def form_valid(self, form):
        rental_pk = self.kwargs.get('pk')
        form.instance.rental_id = rental_pk
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        rental_pk = self.kwargs.get('pk')
        kwargs['initial'] = {'rental': rental_pk}
        return kwargs


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
        current_month = datetime.now().month
        context = super().get_context_data(**kwargs)
        cars = context['object_list']
        for car in cars:
            car.url = reverse('car_detail', args=[car.pk])
            shifts_this_month = Shift.objects.filter(rental__car=car, date__month=current_month)
            # Рассчитываем общее количество отработанных часов за текущий месяц для данной машины
            total_worked_hours = shifts_this_month.aggregate(
                total=Sum(ExpressionWrapper(F('end_time') - F('start_time'), output_field=models.DurationField()))
            )['total']
            # Преобразуем общее количество отработанных часов в число часов
            car.worked_hours_this_month = total_worked_hours.total_seconds() // 3600 if total_worked_hours else 0
        return context


class CarDetailView(DetailView):
    model = Car
    template_name = 'lists/car_detail.html'
    context_object_name = 'car'


class ClientListView(ListView):
    model = Client
    template_name = 'lists/clients.html'
    context_object_name = 'clients'
    paginate_by = 10  # Укажите количество объектов на одной странице

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = context['object_list']
        return context
    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     client_filter = ClientFilter(self.request.GET, queryset=queryset)
    #     return client_filter.qs


class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('rental_calendar')  # Замените 'car_list' на URL вашей страницы после успешного входа

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)