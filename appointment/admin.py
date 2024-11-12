from django.contrib import admin
from .models import Professional, Appointment


admin.site.site_header = 'Scheduling'
admin.site.site_title = 'Administration'
admin.site.index_title = 'Scheduling'


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('start_datetime', 'user', 'professional', 'duration', 'status')
    search_fields = ('user__username', 'professional__name', 'status')
    list_filter = ('status', 'start_datetime')
