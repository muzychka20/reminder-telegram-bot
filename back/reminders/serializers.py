from rest_framework import serializers
from .models import TelegramUser, Reminder


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = '__all__'


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'

class TelegramUserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ['telegram_id', 'name']

class ReminderWithUserSerializer(serializers.ModelSerializer):
    user = TelegramUserMinimalSerializer()
    
    class Meta:
        model = Reminder
        fields = ['id', 'text', 'remind_at', 'is_sent', 'user']