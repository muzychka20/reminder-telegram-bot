from django.contrib import admin
from .models import Reminder, TelegramUser

admin.site.register(TelegramUser)
admin.site.register(Reminder)