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


# class Accounting(models.Model): #
#     date = models.DateField()
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     # Дополнительные поля
