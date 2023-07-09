from django.shortcuts import render
from django.core.cache import cache
from django_redis import get_redis_connection
from .models import Rental


def rental_calendar(request):
    # Проверяем наличие кэша календаря
    calendar = cache.get('rental_calendar')

    if calendar is None:
        print('1')
        # Кэш календаря не найден, получаем данные из модели Rental
        rentals = Rental.objects.all()
        # Формируем словарь с данными для кэша
        rental_dict = {}
        for rental in rentals:
            rental_date = rental.start_date.strftime('%Y-%m-%d')
            if rental_date not in rental_dict:
                rental_dict[rental_date] = []
            rental_dict[rental_date].append(rental)

        # Сохраняем данные в кэше на сутки
        cache.set('rental_calendar', rental_dict, 86400)
    else:
        print('2')
        # Кэш календаря найден, используем его
        rental_dict = calendar

    context = {
        'rentals': rental_dict,
    }
    return render(request, 'rental_calendar.html', context)
