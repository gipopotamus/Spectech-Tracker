from django.contrib import admin
from django_redis import get_redis_connection

from .models import Owner, Leasing, CarType, Car, YRClient, Representative, Worker, ConstructionObject, Shift, Rental


class CarInline(admin.TabularInline):
    model = Car
    extra = 0
    readonly_fields = ['name', 'model', 'car_type', 'number', 'start_date', 'end_date', 'price', 'owner',
                       'fuel_consumption', 'leasing']
    collapse = True
    can_delete = False


class OwnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner_type', 'INN']
    search_fields = ['name', 'INN']
    inlines = [CarInline]


class LeasingAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'amount']
    search_fields = ['name']


class CarTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


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
    ]


class YRClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'documents', 'address', 'black_list', 'representative']
    search_fields = ['full_name', 'documents']
    list_filter = ['black_list']
    autocomplete_fields = ['representative']
    readonly_fields = ['black_list']
    fieldsets = [
        (None, {'fields': ['full_name', 'documents', 'address']}),
        ('Status', {'fields': ['black_list', 'representative']}),
    ]


class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'company', 'INN', 'black_list', 'passport']
    search_fields = ['full_name', 'passport']
    list_filter = ['black_list']
    autocomplete_fields = ['company']
    readonly_fields = ['black_list']
    fieldsets = [
        (None, {'fields': ['full_name', 'company', 'INN']}),
        ('Status', {'fields': ['black_list', 'passport']}),
    ]


class WorkerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'mobile_numer', 'hourly_rate', 'passport']
    search_fields = ['full_name', 'mobile_numer']
    list_filter = ['hourly_rate']


class ConstructionObjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client']
    search_fields = ['name']
    autocomplete_fields = ['client']


class ShiftAdmin(admin.ModelAdmin):
    list_display = ['worker', 'fuel_filled', 'fuel_consumed']
    # search_fields = ['date']
    autocomplete_fields = ['worker']


class RentalAdmin(admin.ModelAdmin):
    list_display = ['client', 'car', 'start_date', 'end_date']
    search_fields = ['start_date']
    autocomplete_fields = ['client', 'car']

    def delete_queryset(self, request, queryset):
        queryset.delete()
        self.clear_cache()

    def clear_cache(self):
        redis_conn = get_redis_connection()
        redis_conn.delete('rental_calendar')


admin.site.register(Owner, OwnerAdmin)
admin.site.register(Leasing, LeasingAdmin)
admin.site.register(CarType, CarTypeAdmin)
admin.site.register(Car, CarAdmin)
admin.site.register(YRClient, YRClientAdmin)
admin.site.register(Representative, RepresentativeAdmin)
admin.site.register(Worker, WorkerAdmin)
admin.site.register(ConstructionObject, ConstructionObjectAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Rental, RentalAdmin)
