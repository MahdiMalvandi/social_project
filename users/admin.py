from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'phone_number']


@admin.register(OtpToken)
class Token(admin.ModelAdmin):
    list_display = ['code', 'user', 'created', 'expired']