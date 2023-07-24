from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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


class CarType(models.Model):
    name = models.CharField('наименование', max_length=100)

    class Meta:
        verbose_name = 'Тип техники'
        verbose_name_plural = 'Тип техники'

    def __str__(self):
        return self.name


class Leasing(models.Model):
    bank = models.CharField('банк', max_length=100)
    amount = models.DecimalField('сумма', max_digits=10, decimal_places=2)
    term = models.IntegerField('срок')
    monthly_payment_date = models.PositiveIntegerField('дата ежемесячного погашения')

    class Meta:
        verbose_name = 'Лизинг'
        verbose_name_plural = 'Лизинг'


class Insurance(models.Model):
    osago_number = models.CharField('номер ОСАГО', max_length=100, blank=True, null=True)
    osago_expiry_date = models.DateField('действует до (ОСАГО)', blank=True, null=True)
    kasko_number = models.CharField('номер КАСКО', max_length=100, blank=True, null=True)
    kasko_expiry_date = models.DateField('действует до (КАСКО)', blank=True, null=True)
    car = models.ForeignKey('Car', verbose_name='техника', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Страховка'
        verbose_name_plural = 'Страховки'


class Car(models.Model):  # техника
    name = models.CharField('наименование', max_length=100)
    model = models.CharField('модель', max_length=100)
    number = models.CharField('номер', max_length=9)
    start_date = models.DateField('дата начала', default=timezone.now)
    end_date = models.DateField('дата окончания', blank=True, null=True)
    price = models.IntegerField('цена')
    owner = models.ForeignKey(Owner, verbose_name='владелец', on_delete=models.CASCADE)
    fuel_consumption = models.DecimalField('расход топлива', max_digits=10, decimal_places=2)
    leasing = models.OneToOneField(Leasing, verbose_name='лизинг', blank=True, null=True, on_delete=models.SET_NULL)
    car_type = models.ForeignKey(CarType, verbose_name='тип техники', on_delete=models.CASCADE)

    # Дополнительные поля
    year_of_manufacture = models.PositiveIntegerField('год выпуска', blank=True, null=True)
    vin = models.CharField('VIN', max_length=17, blank=True, null=True)
    chassis_number = models.CharField('номер шасси', max_length=100, blank=True, null=True)
    body_number = models.CharField('номер кузова', max_length=100, blank=True, null=True)
    engine_number = models.CharField('номер двигателя', max_length=100, blank=True, null=True)
    engine_volume = models.CharField('объем', max_length=50, blank=True, null=True)
    fuel_type = models.CharField('тип топлива', max_length=50, blank=True, null=True)
    fuel_card_number = models.CharField('номер топливной карты', max_length=50, blank=True, null=True)
    inspection_number = models.CharField('Номер ТО', max_length=50, blank=True, null=True)
    inspection_expiry_date = models.DateField('срок действия ТО', blank=True, null=True)

    class Meta:
        verbose_name = 'Технику'
        verbose_name_plural = 'Техника'

    def __str__(self):
        return f"{self.car_type.name} - {self.id}"


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


class BuildObject(models.Model):
    name = models.CharField('название объекта', max_length=100)
    address = models.CharField('адрес объекта', max_length=200)

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'

    def __str__(self):
        return self.name


class Client(PolymorphicModel):
    name = models.CharField('имя/название огранизации', max_length=50)
    build_object = models.ForeignKey('BuildObject', verbose_name='объект', blank=True, on_delete=models.CASCADE)
    email = models.EmailField('email')
    phone = models.CharField('телефон', max_length=15)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, editable=False, null=True)
    object_id = models.PositiveIntegerField(editable=False, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f"{self.name} - {self.get_client_type()}"

    def get_client_type(self):
        return self.content_type

    get_client_type.short_description = 'Тип клиента'

    def save(self, *args, **kwargs):
        # Перед сохранением объекта, устанавливаем соответствующие значения для content_type и object_id
        self.content_type = ContentType.objects.get_for_model(self)
        self.object_id = self.id
        super().save(*args, **kwargs)


class IndividualClient(Client):
    passport = models.CharField('паспорт', max_length=12)

    class Meta:
        verbose_name = 'Физическое лицо'
        verbose_name_plural = 'Физические лица'

    def __str__(self):
        return f"{self.name} "

    def get_client_type(self):
        return "Физическое лицо"


class LegalClient(Client):
    reprasintative_name = models.CharField('имя представителя', max_length=100)
    vat_number = models.CharField('ИНН', max_length=20)

    class Meta:
        verbose_name = 'Юридическое лицо'
        verbose_name_plural = 'Юридические лица'

    def __str__(self):
        return self.name

    def get_client_type(self):
        return "Юридическое лицо"


class Rental(models.Model):  # аренда
    client = models.ForeignKey(Client, verbose_name='клиент', on_delete=models.CASCADE)
    car = models.ForeignKey(Car, verbose_name='техника', on_delete=models.CASCADE)
    start_date = models.DateField('дата начала')
    end_date = models.DateField('дата окончания')
    tariff = models.ForeignKey('Tariff', verbose_name='тариф', on_delete=models.CASCADE, blank=True, null=True)

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
        current_date = self.start_date
        while current_date <= self.end_date:
            cache_key = f"rental_calendar_{current_date.strftime('%Y-%m')}"
            redis_conn.delete(cache_key)
            current_date += relativedelta(months=1)


class Shift(models.Model):  # смена
    worker = models.ForeignKey(Worker, verbose_name='рабочий', on_delete=models.CASCADE)
    fuel_filled = models.DecimalField('заправленное топливо', max_digits=10, decimal_places=2)
    fuel_consumed = models.DecimalField('расход топлива', max_digits=10, decimal_places=2)
    date = models.DateField()  # Добавляем поле даты
    start_time = models.TimeField(verbose_name='время начала')  # Поле времени начала
    end_time = models.TimeField(verbose_name='время окончания')  # Поле времени окончания
    rental = models.ForeignKey(Rental, related_name='shifts', verbose_name='аренда', on_delete=models.CASCADE)

    def __str__(self):
        return f"Смена {self.worker}"

    class Meta:
        verbose_name = 'Смену'
        verbose_name_plural = 'Смены'


class Tariff(models.Model):
    name = models.CharField('название тарифа', max_length=100)
    min_days = models.PositiveIntegerField('минимальное количество дней')
    max_days = models.PositiveIntegerField('максимальное количество дней')
    price = models.DecimalField('цена', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.name

# class Accounting(models.Model): #
#     date = models.DateField()
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     # Дополнительные поля

=======
from django.db import models
from django.utils import timezone


class Owner(models.Model): #владелец
    owner_type = models.CharField(max_length=20)
    name = models.CharField(max_length=20)
    INN = models.IntegerField()


class Leasing(models.Model): #лизинг
    name = models.CharField()
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.IntegerField()


class CarType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Car(models.Model): #техника
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    number = models.CharField(max_length=9)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    price = models.IntegerField()
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    fuel_consumption = models.DecimalField(max_digits=10, decimal_places=2)
    leasing = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.car_type.name} - {self.id}"

    @staticmethod
    def get_car_choices():
        return [(type_obj.id, type_obj.name) for type_obj in CarType.objects.all()]

    @classmethod
    def get_car_choices(cls):
        return [(type_obj.id, type_obj.name) for type_obj in
                cls._meta.get_field('car_type').remote_field.model.objects.all()]


class YRClient(models.Model):  #юр лицо - клиент
    full_name = models.CharField(max_length=100)
    documents = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    black_list = models.BooleanField(default=False)
    representative = models.ForeignKey('representative', on_delete=models.CASCADE)
    # Дополнительные поля


class Representative(models.Model):   #физ лицо/представитель юр лица
    full_name = models.CharField(max_length=100)
    company = models.ForeignKey(YRClient, related_name='Representative_name', on_delete=models.CASCADE)
    INN = models.IntegerField()
    black_list = models.BooleanField(default=False)
    passport = models.CharField()


class Worker(models.Model): #рабочий-оператор
    full_name = models.CharField()
    mobile_numer = models.CharField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    passport = models.CharField()


class ConstructionObject(models.Model): #объект стройки
    name = models.CharField(max_length=100)
    client = models.ForeignKey('YRClient', on_delete=models.CASCADE, related_name='construction_objects')


class Shift(models.Model): #смена
    date = models.DateField()
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    fuel_filled = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_consumed = models.DecimalField(max_digits=10, decimal_places=2)
    rental = models.ForeignKey('Rental', on_delete=models.CASCADE, related_name='shifts')


class Rental(models.Model): #аренда
    client = models.ForeignKey(YRClient, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    # Дополнительные поля

