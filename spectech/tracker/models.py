from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django_redis import get_redis_connection

User = get_user_model()
#TODO: поправить овнера
#TODO: добавить свободный файл в загрузку
#TODO: добавить несколько документов одного типа


# Модель для хранения информации о владельце техники
class Owner(models.Model):
    owner_type = models.CharField('Тип владельца', max_length=20)
    name = models.CharField('Наименование', max_length=20)
    inn = models.CharField('ИНН', max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Владельца'
        verbose_name_plural = 'Владельцы'


# Модель для хранения информации о типе техники
class CarType(models.Model):
    name = models.CharField('Наименование', max_length=100)

    class Meta:
        verbose_name = 'Тип техники'
        verbose_name_plural = 'Тип техники'

    def __str__(self):
        return self.name


# Модель для хранения информации о лизинге
class Leasing(models.Model):
    bank = models.CharField('Банк', max_length=100)
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    term = models.IntegerField('Срок')
    monthly_payment_date = models.PositiveIntegerField('Дата ежемесячного погашения')

    class Meta:
        verbose_name = 'Лизинг'
        verbose_name_plural = 'Лизинг'

    def __str__(self):
        return f"{self.bank} - {self.amount}"


# Модель для хранения информации о страховке
class Insurance(models.Model):
    osago_number = models.CharField('Номер ОСАГО', max_length=100, blank=True, null=True)
    osago_expiry_date = models.DateField('Действует до (ОСАГО)', blank=True, null=True)
    kasko_number = models.CharField('Номер КАСКО', max_length=100, blank=True, null=True)
    kasko_expiry_date = models.DateField('Действует до (КАСКО)', blank=True, null=True)
    car = models.ForeignKey('Car', verbose_name='Техника', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Страховка'
        verbose_name_plural = 'Страховки'


# Модель для хранения информации о технике
class Car(models.Model):
    name = models.CharField('Наименование', max_length=100)
    model = models.CharField('Модель', max_length=100)
    number = models.CharField('Номер', max_length=9)
    start_date = models.DateField('Дата начала', default=timezone.now)
    end_date = models.DateField('Дата окончания', blank=True, null=True)
    price = models.IntegerField('Цена')
    owner = models.ForeignKey(Owner, verbose_name='Владелец', on_delete=models.CASCADE)
    fuel_consumption = models.DecimalField('Расход топлива', max_digits=10, decimal_places=2)
    leasing = models.OneToOneField(Leasing, verbose_name='Лизинг', blank=True, null=True, on_delete=models.SET_NULL)
    car_type = models.ForeignKey(CarType, verbose_name='Тип техники', on_delete=models.CASCADE)
    work_mode = models.CharField(verbose_name='Доп. режим работы', blank=True, null=True, max_length=5)

    # Дополнительные поля
    year_of_manufacture = models.PositiveIntegerField('Год выпуска', blank=True, null=True)
    vin = models.CharField('VIN', max_length=17, blank=True, null=True)
    chassis_number = models.CharField('Номер шасси', max_length=100, blank=True, null=True)
    body_number = models.CharField('Номер кузова', max_length=100, blank=True, null=True)
    engine_number = models.CharField('Номер двигателя', max_length=100, blank=True, null=True)
    engine_volume = models.CharField('Объем', max_length=50, blank=True, null=True)
    fuel_type = models.CharField('Тип топлива', max_length=50, blank=True, null=True)
    fuel_card_number = models.CharField('Номер топливной карты', max_length=50, blank=True, null=True)
    inspection_number = models.CharField('Номер ТО', max_length=50, blank=True, null=True)
    inspection_expiry_date = models.DateField('Срок действия ТО', blank=True, null=True)

    class Meta:
        verbose_name = 'Технику'
        verbose_name_plural = 'Техника'

    def __str__(self):
        return f"{self.car_type.name} - {self.number}"


# Модель для хранения информации о рабочих-операторах
class Worker(models.Model):
    full_name = models.CharField('Полное имя', max_length=50)
    mobile_numer = models.CharField('Мобильный номер', max_length=50)
    hourly_rate = models.DecimalField('Почасовая ставка', max_digits=10, decimal_places=2)
    passport = models.CharField('Паспорт', max_length=50)

    class Meta:
        verbose_name = 'Оператора'
        verbose_name_plural = 'Операторы'

    def __str__(self):
        return self.full_name


# Модель для хранения информации об объектах строительства
class BuildObject(models.Model):
    name = models.CharField('Название объекта', max_length=100)
    address = models.CharField('Адрес объекта', max_length=200)
    client = models.ForeignKey('Client', verbose_name='Клиент', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'

    def __str__(self):
        return self.name


# Модель для хранения информации о клиентах
class Client(PolymorphicModel):
    name = models.CharField('Имя/Название огранизации', max_length=50)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=15)

    # Поля для реализации полиморфизма
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, editable=False, null=True)
    object_id = models.PositiveIntegerField(editable=False, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f"{self.name} - {self.get_client_type()}"

    # Метод для получения типа клиента
    def get_client_type(self):
        return self.content_type

    get_client_type.short_description = 'Тип клиента'

    def save(self, *args, **kwargs):
        # Перед сохранением объекта, устанавливаем соответствующие значения для content_type и object_id
        self.content_type = ContentType.objects.get_for_model(self)
        self.object_id = self.id
        super().save(*args, **kwargs)


# Модель для хранения информации о физических лицах
class IndividualClient(Client):
    passport = models.CharField('Паспорт', max_length=12)

    class Meta:
        verbose_name = 'Физическое лицо'
        verbose_name_plural = 'Физические лица'

    def __str__(self):
        return f"{self.name} "

    def get_client_type(self):
        return "Физическое лицо"


# Модель для хранения информации о юридических лицах
class LegalClient(Client):
    reprasintative_name = models.CharField('Имя представителя', max_length=100)
    vat_number = models.CharField('ИНН', max_length=20)

    class Meta:
        verbose_name = 'Юридическое лицо'
        verbose_name_plural = 'Юридические лица'

    def __str__(self):
        return self.name

    def get_client_type(self):
        return "Юридическое лицо"


# Модель для хранения информации об аренде
class Rental(models.Model):
    client = models.ForeignKey(Client, verbose_name='Клиент', on_delete=models.CASCADE)
    car = models.ForeignKey(Car, verbose_name='Техника', on_delete=models.CASCADE)
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    manager = models.ForeignKey(User, verbose_name='Менеджер', on_delete=models.CASCADE)
    build_object = models.ForeignKey(BuildObject, verbose_name='Объект', on_delete=models.CASCADE, blank=True, null=True)
    tariff = models.IntegerField('Цена(час)', blank=True, null=True)
    extra_tariff = models.IntegerField('Цена(доп.режим работы)', blank=True, null=True)

    contract_file = models.FileField(verbose_name='Договор', upload_to='rental_files/', null=True, blank=True)
    invoice_file = models.FileField(verbose_name='Счет', upload_to='rental_files/', null=True, blank=True)
    upd_file = models.FileField(verbose_name='УПД', upload_to='rental_files/', null=True, blank=True)
    esm7_file = models.FileField(verbose_name='ЭСМ-7', upload_to='rental_files/', null=True, blank=True)
    waybill_file = models.FileField(verbose_name='Путевой лист', upload_to='rental_files/', null=True, blank=True)

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

    # Метод для очистки кэша
    def clear_cache(self):
        redis_conn = get_redis_connection()
        current_date = self.start_date
        while current_date <= self.end_date:
            cache_key = f"rental_calendar_{current_date.strftime('%Y-%m')}"
            redis_conn.delete(cache_key)
            current_date += relativedelta(months=1)


# Модель для хранения информации о сменах
class Shift(models.Model):
    worker = models.ForeignKey(Worker, verbose_name='Рабочий', on_delete=models.CASCADE)
    date = models.DateField()  # Добавляем поле даты
    start_time = models.TimeField(verbose_name='Время начала')  # Поле времени начала
    end_time = models.TimeField(verbose_name='Время окончания')  # Поле времени окончания
    rental = models.ForeignKey(Rental, related_name='shifts', verbose_name='Аренда', on_delete=models.CASCADE)
    is_additional_mode = models.BooleanField('Дополнительный режим', default=False)
    dinner = models.BooleanField('Обед', default=False)

    def __str__(self):
        return f"Смена {self.worker}"

    class Meta:
        verbose_name = 'Смену'
        verbose_name_plural = 'Смены'
