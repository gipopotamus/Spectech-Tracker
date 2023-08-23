from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django_redis import get_redis_connection

from .models import Owner, Leasing, CarType, Car, Worker, BuildObject, Shift, Rental, Insurance, IndividualClient, \
    LegalClient, Tariff, Client


class CarInline(admin.TabularInline):
    model = Car
    extra = 0
    fields = ['name']
    readonly_fields = ['name']
    collapse = True
    can_delete = False


class OwnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner_type', 'inn']
    search_fields = ['name', 'inn']
    inlines = [CarInline]


class LeasingAdmin(admin.ModelAdmin):
    list_display = ('id', 'bank', 'amount', 'term', 'monthly_payment_date')
    list_filter = ('term',)
    search_fields = ('bank', 'amount')


class CarTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class InsuranceInline(admin.StackedInline):
    model = Insurance
    can_delete = False
    extra = 1


class CarAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'car_type', 'number', 'start_date', 'end_date', 'price', 'owner', 'leasing']
    list_filter = ['leasing']
    search_fields = ['name', 'model', 'number', 'car_type']
    autocomplete_fields = ['owner']
    readonly_fields = ['start_date']
    fieldsets = [
        (None, {'fields': ['name', 'model', 'number', 'car_type']}),
        ('Dates', {'fields': ['start_date', 'end_date']}),
        ('Details', {'fields': ['price', 'owner', 'fuel_consumption', 'leasing']}),
        ('Additional', {
            'classes': ('collapse',),
            'fields': [
                'year_of_manufacture',
                'vin',
                'chassis_number',
                'body_number',
                'engine_number',
                'engine_volume',
                'fuel_type',
                'fuel_card_number',
                'inspection_number',
                'inspection_expiry_date',
            ],
        }),
    ]
    inlines = [InsuranceInline]


class BuildObjectInline(admin.StackedInline):
    model = BuildObject
    extra = 1


class IndividualClientAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    inlines = [BuildObjectInline]


class LegalClientAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    inlines = [BuildObjectInline]


class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_client_type']
    search_fields = ['name']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Получаем объект клиента
        client = self.get_object(request, object_id)

        # Проверяем тип клиента
        if isinstance(client, IndividualClient):
            # Получаем URL для страницы редактирования физического лица
            url = reverse('admin:%s_%s_change' % (self.model._meta.app_label, 'individualclient'), args=[object_id])
            return HttpResponseRedirect(url)
        elif isinstance(client, LegalClient):
            # Получаем URL для страницы редактирования юридического лица
            url = reverse('admin:%s_%s_change' % (self.model._meta.app_label, 'legalclient'), args=[object_id])
            return HttpResponseRedirect(url)
        else:
            return super().change_view(request, object_id, form_url, extra_context)


class WorkerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'mobile_numer', 'hourly_rate', 'passport']
    search_fields = ['full_name', 'mobile_numer']
    list_filter = ['hourly_rate']


class BuildObjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client']
    search_fields = ['name']
    list_filter = ['client']


class ShiftAdmin(admin.ModelAdmin):
    list_display = ['worker', 'fuel_filled', 'fuel_consumed']
    # search_fields = ['date']
    autocomplete_fields = ['worker']


class TariffAdmin(admin.ModelAdmin):
    search_fields = ['name']  # Добавьте поле для поиска тарифов


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0
    readonly_fields = ['worker', 'fuel_filled', 'fuel_consumed', 'date', 'start_time', 'end_time']


class RentalAdmin(admin.ModelAdmin):
    list_display = ['client', 'car', 'start_date', 'end_date', 'tariff']
    list_filter = ['start_date', 'end_date']
    autocomplete_fields = ['client', 'car', 'tariff']
    inlines = [ShiftInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Проверяем, что объект не сохранен (новый объект)
            obj.manager = request.user
        super().save_model(request, obj, form, change)

    def delete_queryset(self, request, queryset):
        queryset.delete()
        self.clear_cache()

    def clear_cache(self):
        redis_conn = get_redis_connection()
        current_date = self.start_date
        while current_date <= self.end_date:
            cache_key = f"rental_calendar_{current_date.strftime('%Y-%m')}"
            redis_conn.delete(cache_key)
            current_date += relativedelta(months=1)


admin.site.register(Owner, OwnerAdmin)
admin.site.register(Leasing)
admin.site.register(CarType, CarTypeAdmin)
admin.site.register(Car, CarAdmin)
admin.site.register(IndividualClient, IndividualClientAdmin)
admin.site.register(LegalClient, LegalClientAdmin)
admin.site.register(Worker, WorkerAdmin)
admin.site.register(BuildObject, BuildObjectAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Rental, RentalAdmin)
admin.site.register(Tariff, TariffAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.site_header = 'Панель администратора'
