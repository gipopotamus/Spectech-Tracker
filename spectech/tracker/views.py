import json
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django_redis import get_redis_connection
from .models import Rental, Car


def rental_calendar(request):
    # Получаем текущую дату и время
    today = timezone.now().date()
    # Формируем список дат на основе текущей даты и следующих 30 дней
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    # Получаем подключение к Redis
    redis_conn = get_redis_connection()
    # Проверяем наличие кэша календаря в Redis
    calendar = redis_conn.get('rental_calendar')
    if calendar is None:
        # Кэш календаря не найден в Redis, получаем данные из модели Rental
        rentals = Rental.objects.all()
        # Формируем словарь с забронированными датами для каждого автомобиля
        booked_dates = {}
        cars = Car.objects.all()
        for car in cars:
            booked_dates[car.name] = []
        for rental in rentals:
            car_name = rental.car.name
            rental_data = {
                 rental.id: [date.strftime('%Y-%m-%d') for date in
                                (rental.start_date + timedelta(days=i) for i in
                                    range((rental.end_date - rental.start_date).days + 1))]}
            booked_dates[car_name].append(rental_data)
        # Сохраняем данные в кэше Redis на сутки
        redis_conn.set('rental_calendar', json.dumps(booked_dates), ex=86400)
    else:
        # Кэш календаря найден в Redis, преобразуем его обратно в словарь
        booked_dates = json.loads(calendar)

    context = {
        'dates': dates,
        'booked_dates': booked_dates,
    }
    print(context)
    return render(request, 'rental_calendar.html', context)
