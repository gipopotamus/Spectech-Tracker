from django.db import models
from django.utils import timezone


#TODO: update models, add documents
from django_redis import get_redis_connection


class Owner(models.Model):  # владелец
    owner_type = models.CharField('тип владельца', max_length=20)
    name = models.CharField('наименование', max_length=20)
    INN = models.IntegerField('ИНН')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Владельца'
        verbose_name_plural = 'Владельцы'


class Leasing(models.Model):  # лизинг
    name = models.CharField('наименование', max_length=50)
    start_date = models.DateField('дата начала')
    end_date = models.DateField('дата окончания')
    amount = models.IntegerField('сумма')

    class Meta:
        verbose_name = 'Лизинг'
        verbose_name_plural = 'Лизинг'


class CarType(models.Model):
    name = models.CharField('наименование', max_length=100)

    class Meta:
        verbose_name = 'Тип техники'
        verbose_name_plural = 'Тип техники'


    def __str__(self):
        return self.name


class Car(models.Model):  # техника
    name = models.CharField('наименование', max_length=100)
    model = models.CharField('модель', max_length=100)
    number = models.CharField('номер', max_length=9)
    start_date = models.DateField('дата начала', default=timezone.now)
    end_date = models.DateField('дата окончания')
    price = models.IntegerField('цена')
    owner = models.ForeignKey(Owner, verbose_name='владелец', on_delete=models.CASCADE)
    fuel_consumption = models.DecimalField('расход топлива', max_digits=10, decimal_places=2)
    leasing = models.BooleanField('лизинг', default=False)
    car_type = models.ForeignKey(CarType, verbose_name='тип техники', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Технику'
        verbose_name_plural = 'Техника'

    def __str__(self):
        return f"{self.car_type.name} - {self.id}"

    # @staticmethod
    # def get_car_choices():
    #     return [(type_obj.id, type_obj.name) for type_obj in CarType.objects.all()]
    #
    # @classmethod
    # def get_car_choices(cls):
    #     return [(type_obj.id, type_obj.name) for type_obj in
    #             cls._meta.get_field('car_type').remote_field.model.objects.all()]


class YRClient(models.Model):  # юр лицо - клиент
    full_name = models.CharField('полное имя', max_length=100)
    documents = models.CharField('документы', max_length=100)
    address = models.CharField('адрес', max_length=100)
    black_list = models.BooleanField('в черном списке', default=False)
    representative = models.ForeignKey('representative', verbose_name='представитель', on_delete=models.CASCADE,
                                       null=True, blank=True)
    # Дополнительные поля

    class Meta:
        verbose_name = 'Юр.Лицо'
        verbose_name_plural = 'Юр.Лица'

    def __str__(self):
        return self.full_name


class Representative(models.Model):  # физ лицо/представитель юр лица
    full_name = models.CharField('имя', max_length=100)
    company = models.ForeignKey(YRClient, verbose_name='компания', related_name='Representative_name',
                                on_delete=models.CASCADE, null=True, blank=True)
    INN = models.IntegerField('ИНН')
    black_list = models.BooleanField('в черном списке', default=False)
    passport = models.CharField('паспорт', max_length=50)

    class Meta:
        verbose_name = 'Физ.Лицо/представитель'
        verbose_name_plural = 'Физ.Лицо/представитель'


class Worker(models.Model):  # рабочий-оператор
    full_name = models.CharField('полное имя', max_length=50)
    mobile_numer = models.CharField('мобильный номер', max_length=50)
    hourly_rate = models.DecimalField('почасовая ставка', max_digits=10, decimal_places=2)
    passport = models.CharField('паспорт', max_length=50)

    class Meta:
        verbose_name = 'Оператора'
        verbose_name_plural = 'Операторы'

    def __str__(self):
        return self.full_name


class ConstructionObject(models.Model):  # объект стройки
    name = models.CharField('наименование', max_length=100)
    client = models.ForeignKey('YRClient', verbose_name='клиент', on_delete=models.CASCADE,
                               related_name='construction_objects')

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'


class Shift(models.Model):  # смена
    worker = models.ForeignKey(Worker, verbose_name='рабочий', on_delete=models.CASCADE)
    fuel_filled = models.DecimalField('заправленное топливо', max_digits=10, decimal_places=2)
    fuel_consumed = models.DecimalField('расход топлива', max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def total_salary(self):
        days = (self.end_date - self.start_date).days + 1
        return self.worker.hourly_rate * days

    def __str__(self):
        return f" Смена {self.worker}"

    class Meta:
        verbose_name = 'Смену'
        verbose_name_plural = 'Смены'


class Rental(models.Model):  # аренда
    client = models.ForeignKey(YRClient, verbose_name='клиент', on_delete=models.CASCADE)
    car = models.ForeignKey(Car, verbose_name='техника', on_delete=models.CASCADE)
    start_date = models.DateField('дата начала')
    end_date = models.DateField('дата окончания')
    shifts = models.ManyToManyField(Shift)
    # Дополнительные поля

    class Meta:
        verbose_name = 'Аренду'
        verbose_name_plural = 'Аренды'

    def __str__(self):
        return f'{self.start_date},{self.end_date}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.clear_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.clear_cache()

    def clear_cache(self):
        redis_conn = get_redis_connection()
        redis_conn.delete('rental_calendar')


# class Accounting(models.Model): #
#     date = models.DateField()
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     # Дополнительные поля