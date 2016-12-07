from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gerencex.core.models import UserDetail, Timing, Restday, HoursBalance, Absences, Office


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserDetailInLine(admin.TabularInline):
    model = UserDetail
    can_delete = False
    verbose_name_plural = 'detalhes'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserDetailInLine, )


class TimingAdmin(admin.ModelAdmin):
    list_display = ('date_time', 'user', 'checkin', 'created_by', 'client_ip', 'client_local_ip')
    list_filter = ('date_time', 'user', 'created_by')
    date_hierarchy = 'date_time'


class RestdayAdmin(admin.ModelAdmin):
    list_display = ('date', 'note', 'work_hours')
    list_filter = ('date',)
    date_hierarchy = 'date'


class HoursBalanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'time_credit', 'time_debit', 'time_balance')
    list_filter = ('date', 'user')
    date_hierarchy = 'date'


class AbsencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'cause', 'credit', 'debit')
    list_filter = ('user',)
    date_hierarchy = 'date'


class OfficeAdmin(admin.ModelAdmin):
    list_display = ('initials', 'name', 'active')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register your models here.

admin.site.register(Timing, TimingAdmin)
admin.site.register(Restday, RestdayAdmin)
admin.site.register(HoursBalance, HoursBalanceAdmin)
admin.site.register(Absences, AbsencesAdmin)
admin.site.register(Office, OfficeAdmin)