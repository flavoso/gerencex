from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gerencex.core.models import UserDetail, Timing, Restday, HoursBalance


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
    list_display = ('date_time', 'user', 'checkin', 'created_by')
    list_filter = ('date_time', 'user', 'created_by')
    date_hierarchy = 'date_time'


class RestdayAdmin(admin.ModelAdmin):
    list_display = ('date', 'note', 'work_hours')
    list_filter = ('date',)


class HoursBalanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'credit', 'debit', 'balance')
    list_filter = ('date', 'user')
    date_hierarchy = 'date'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register your models here.

admin.site.register(Timing, TimingAdmin)
admin.site.register(Restday, RestdayAdmin)
admin.site.register(HoursBalance, HoursBalanceAdmin)
