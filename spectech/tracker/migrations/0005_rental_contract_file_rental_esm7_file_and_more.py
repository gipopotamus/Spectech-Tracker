# Generated by Django 4.2.3 on 2023-08-23 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0004_rental_contract_file_rental_esm7_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='vin',
            field=models.CharField(blank=True, max_length=25, null=True, verbose_name='VIN'),
        ),
        migrations.AlterField(
            model_name='leasing',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name='сумма'),
        ),
        migrations.AlterField(
            model_name='owner',
            name='INN',
            field=models.CharField(max_length=15, verbose_name='ИНН'),
        ),
        migrations.AlterField(
            model_name='owner',
            name='name',
            field=models.CharField(max_length=40, verbose_name='наименование'),
        ),
    ]