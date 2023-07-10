from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django_redis import get_redis_connection
from .models import Rental

def rental_calendar(request):
    # Получаем текущую дату и время
    today = timezone.now().date()

    # Формируем список дат на основе текущей даты и следующих 30 дней
    dates = [today + timedelta(days=i) for i in range(31)]

    # Получаем подключение к Redis
    redis_conn = get_redis_connection()

    # Проверяем наличие кэша календаря в Redis
    calendar = redis_conn.get('rental_calendar')

    if calendar is None:
        # Кэш календаря не найден в Redis, получаем данные из модели Rental
        rentals = Rental.objects.all()

        # Формируем словарь с забронированными датами для каждого автомобиля
        booked_dates = {}
        for rental in rentals:
            if rental not in booked_dates:
                booked_dates[rental] = [rental.start_date]
            # Добавляем также промежуточные даты между началом и концом аренды
            current_date = rental.start_date + timedelta(days=1)
            temp = [rental.start_date]
            while current_date <= rental.end_date:
                temp.append(current_date)
                current_date += timedelta(days=1)
            booked_dates[rental].append(temp)

        # Сохраняем данные в кэше Redis на сутки
        redis_conn.set('rental_calendar', str(booked_dates), ex=86400)
    else:
        # Кэш календаря найден в Redis, преобразуем его обратно в словарь
        booked_dates = eval(calendar)

    context = {
        'dates': dates,
        'booked_dates': booked_dates,
    }

    return render(request, 'rental_calendar.html', context)
