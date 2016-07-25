from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gerencex.core.models import UserDetail

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserDetailInLine(admin.StackedInline):
    model = UserDetail
    can_delete = False
    verbose_name_plural = 'detalhes'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserDetailInLine, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



# Register your models here.
# from gerencex.core.models import UserDetail
#
# admin.site.register(UserDetail)