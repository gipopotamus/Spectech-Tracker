from django.contrib.auth import logout
from django.db import models
from django.contrib.auth.views import LoginView
from django.db.models import Sum, F, ExpressionWrapper, FloatField, When, Value, IntegerField, Case
from django.db.models.functions import ExtractHour
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.views import View
from django.views.generic import DetailView, ListView, CreateView
import calendar as cal
from .forms import RentalForm, ShiftForm, DocumentForm
from .models import Car, Rental, Shift, Client, BuildObject
from datetime import timedelta
from .services import generate_excel, CalendarService
#TODO обновить календарь


class RentalCalendarView(View):
    template_name = 'rental_calendar.html'

    def get_first_and_last_day_of_month(self, date):
        first_day = date.replace(day=1)
        last_day = date.replace(day=1) + timedelta(days=32)
        last_day = last_day.replace(day=1) - timedelta(days=1)
        return first_day, last_day

    def get(self, request, *args, **kwargs):
        selected_month = self.request.GET.get('month')
        if not selected_month:
            current_month = timezone.now().strftime('%Y-%m')
            return redirect(reverse('rental_calendar') + f'?month={current_month}')

        booked_dates = CalendarService.get_booked_dates(selected_month)

        selected_date = timezone.datetime.strptime(selected_month, '%Y-%m').date()
        num_days_in_month = cal.monthrange(selected_date.year, selected_date.month)[1]

        context = {
            'dates': [(selected_date + timedelta(days=i)).strftime('%m-%d') for i in range(num_days_in_month)],
            'booked_dates': booked_dates,
            'form': RentalForm(),
            'selected_month': selected_date.strftime('%Y-%m'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = RentalForm(request.POST)
        selected_month = self.request.GET.get('month')
        if form.is_valid():
            rental = form.save()
            return redirect('rental_calendar')
        else:
            context = self.get_context_data(selected_month)
            context['form'] = form
            return render(request, self.template_name, context)


def get_build_objects(request):
    if request.method == 'GET':
        client_id = request.GET.get('client_id')
        build_objects = BuildObject.objects.filter(client_id=client_id).values('id', 'name', 'address')
        return JsonResponse(list(build_objects), safe=False)


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
        shifts = rental.shifts.annotate(
            total_hours=ExpressionWrapper(
                ExtractHour(F('end_time') - F('start_time')) -
                Case(
                    When(dinner=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                output_field=FloatField()  # Используем FloatField для временной разницы
            ),
            total_payment=ExpressionWrapper(
                (ExtractHour(F('end_time') - F('start_time')) -
                 Case(
                     When(dinner=True, then=Value(1)),
                     default=Value(0),
                     output_field=IntegerField(),
                 )) * F('worker__hourly_rate'),
                output_field=FloatField()  # Используем FloatField для оплаты смены
            )
        )
        total_salary = shifts.aggregate(total_salary=Sum('total_payment'))['total_salary'] or 0
        context['shift_form'] = ShiftForm(initial={'rental': self.object.pk})
        context['shifts'] = shifts
        context['total_salary'] = total_salary
        context['document_form'] = DocumentForm()
        return context

    def post(self, request, *args, **kwargs):
        rental = self.get_object()
        document_form = DocumentForm(request.POST, request.FILES)
        shift_form = ShiftForm(request.POST)
        if document_form.is_valid():
            # Обрабатываем каждый загружаемый файл отдельно
            for field_name, file in request.FILES.items():
                # Получаем соответствующее поле модели Rental по его имени
                field = getattr(rental, field_name)

                # Сохраняем файл в соответствующее поле модели Rental
                field.save(file.name, file, save=True)
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
        context['from_list'] = self.request.GET.get('from_list', False)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car = self.get_object()

        # Получение всех связанных страховок
        context['insurances'] = car.insurance_set.all()
        return context


class ClientListView(ListView):
    model = Client
    template_name = 'lists/clients.html'
    context_object_name = 'clients'
    paginate_by = 10  # Укажите количество объектов на одной странице

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = context['object_list']
        for client in clients:
            client.url = reverse('client_detail', args=[client.pk])
        return context
    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     client_filter = ClientFilter(self.request.GET, queryset=queryset)
    #     return client_filter.qs


class ClientDetailView(DetailView):
    model = Client
    template_name = 'lists/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        context['build_objects'] = client.build_objects.all()
        return context


class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('rental_calendar')  # Замените 'car_list' на URL вашей страницы после успешного входа

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)


def logout_view(request):
    logout(request)
    return redirect('login')


def special_equipment_info(request):
    if request.method == 'POST':
        selected_month = request.POST.get('selected_month')
        try:
            selected_date = datetime.strptime(selected_month, '%Y-%m')
        except ValueError:
            selected_date = datetime.now()

        # Генерируем и загружаем Excel-файл
        response = generate_excel(request, selected_date)  # Передаем объект запроса и выбранный месяц
        return response

    else:
        selected_date = datetime.now()

    return render(request, 'special_equipment_info.html', {'selected_month': selected_date.strftime('%Y-%m')})
