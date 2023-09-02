import json
from datetime import timedelta
from openpyxl.styles import Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django_redis import get_redis_connection
from .models import Rental, Car, Shift, BuildObject
from .forms import DocumentForm
import calendar


def upload_documents(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    if request.method == 'POST':
        document_form = DocumentForm(request.POST, request.FILES)
        if document_form.is_valid():
            # Сохраняем каждый загружаемый файл отдельно
            for field_name, file in request.FILES.items():
                # Получаем соответствующее поле модели Rental по его имени
                field = getattr(rental, field_name)
                # Сохраняем файл в соответствующее поле модели Rental
                field.save(file.name, file, save=True)

            # После успешной загрузки документов, перенаправляем на страницу с деталями аренды
            return redirect('rental_detail', pk=pk)  # Замените 'rental_detail' на ваш URL pattern

        else:
            # Если форма невалидна, вернем ошибку с соответствующим статусом
            # и передадим параметры ошибки в URL для дальнейшего отображения на странице
            error_params = "?error=invalid_form"
            return redirect('rental_detail', pk=pk) + error_params  # Замените 'rental_detail' на ваш URL pattern

    # Если метод запроса не POST, вернем ошибку с соответствующим статусом
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


def generate_excel(request, selected_date):
    start_date = selected_date.replace(day=1)
    end_date = start_date.replace(month=start_date.month % 12 + 1, day=1)

    # Get the number of days in the selected month
    _, num_days = calendar.monthrange(selected_date.year, selected_date.month)

    # Create a new Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Special Equipment Report'

    # Set font style
    bold_font = Font(bold=True)

    # Set fill styles
    green_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    # Add headers with styles
    headers = ['Номер', 'Техника', 'Тариф', 'Наименование и адрес объекта']
    for day in range(1, num_days + 1):
        headers.append(day)
    headers += ['количество часов', 'всего (р.)']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = bold_font

    # Fetch data and populate rows
    cars = Car.objects.all()
    row_number = 1

    for car in cars:
        shifts = Shift.objects.filter(rental__car=car, date__range=(start_date, end_date))
        shifts_by_day = {shift.date.day: shift for shift in shifts}

        for shift in shifts:
            row_data = [row_number, car.name]
            if shift.rental.tariff:
                row_data.append(shift.rental.tariff.hourly_rate)
            else:
                row_data.append('')
            row_data.append(shift.rental.build_object.name if shift.rental.build_object else '')
            total_hours = 0
            total_income = 0

            for day in range(1, num_days + 1):
                day_shift = shifts_by_day.get(day)
                if day_shift and day_shift.rental == shift.rental:
                    hours = (day_shift.end_time.hour - day_shift.start_time.hour) + (
                            day_shift.end_time.minute - day_shift.start_time.minute) / 60
                    total_hours += hours
                    total_income += hours * (shift.rental.tariff.hourly_rate if shift.rental.tariff else 2)
                    row_data.append(hours)
                    if hours > 0:
                        row_data[-1] = hours  # Set green fill for cells with hours
                else:
                    row_data.append(0)
            row_data += [total_hours, total_income]
            ws.append(row_data)

            # Apply inner border to each row
            for cell in ws[row_number + 1]:
                if cell.value == 0:
                    cell.fill = red_fill  # Set red fill for cells with zero hours

            row_number += 1

    # Identify cars with no shifts in the selected month
    cars_with_shifts = [shift.rental.car for shift in Shift.objects.filter(date__range=(start_date, end_date))]
    cars_without_shifts = [car for car in cars if car not in cars_with_shifts]

    # Add rows for cars with no shifts
    for car in cars_without_shifts:
        row_data = [row_number, car.name, '', '']
        for _ in range(num_days + 2):
            row_data.append(0)
        row_data += ['', '--']  # Add empty values for tariff and total price columns
        ws.append(row_data)

        # Apply red fill to cells
        for cell in ws[row_number + 1]:
            cell.fill = red_fill

        row_number += 1

    for column in ws.columns:
        max_length = 0
        column_name = get_column_letter(column[0].column)  # Get the column name (e.g., A, B, C)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2) * 1.5  # Adjusting width with a little extra space
        ws.column_dimensions[column_name].width = adjusted_width

    response = HttpResponse(content_type='application/ms-excel')
    response[
        'Content-Disposition'] = f'attachment; filename=TCA_Report_{selected_date.strftime("%Y-%m")}.xlsx'
    wb.save(response)

    return response


class CalendarService:
    @staticmethod
    def get_booked_dates(selected_month):
        redis_conn = get_redis_connection()
        cache_key = f"rental_calendar_{selected_month}"
        calendar = redis_conn.get(cache_key)

        if calendar:
            return json.loads(calendar)
        else:
            return CalendarService.calculate_and_cache_booked_dates(selected_month)

    @staticmethod
    def calculate_and_cache_booked_dates(selected_month):
        selected_date = timezone.datetime.strptime(selected_month, '%Y-%m').date()
        first_day_of_month = selected_date.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        rentals = Rental.objects.filter(
            end_date__gte=first_day_of_month,
            start_date__lte=last_day_of_month
        )

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

        redis_conn = get_redis_connection()
        cache_key = f"rental_calendar_{selected_month}"
        redis_conn.set(cache_key, json.dumps(booked_dates), ex=3600)

        return booked_dates
