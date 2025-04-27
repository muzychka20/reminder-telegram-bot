from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser, Reminder
from django.utils import timezone
from .serializers import ReminderWithUserSerializer, ReminderSerializer
from rest_framework.permissions import AllowAny
from dateutil import parser
import datetime


class RegisterUserView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        name = request.data.get('name')

        user, created = TelegramUser.objects.get_or_create(telegram_id=telegram_id)
        if created:
            user.name = name
            user.save()

        return Response({'success': True})


class CreateReminderView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        text = request.data.get('text')
        remind_at = request.data.get('remind_at')

        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
            Reminder.objects.create(user=user, text=text, remind_at=remind_at)
            return Response({'success': True})
        except TelegramUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class ListRemindersView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, telegram_id):
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
            time_format_24h = user.time_format_24h
        except TelegramUser.DoesNotExist:
            time_format_24h = True
            
        reminders = Reminder.objects.filter(user__telegram_id=telegram_id, is_sent=False)
        
        serializer = ReminderSerializer(reminders, many=True)
        data = serializer.data
        
        for reminder in data:
            if 'remind_at' in reminder:
                dt = parser.parse(reminder['remind_at'])
                
                if time_format_24h:
                    reminder['remind_at'] = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    reminder['remind_at'] = dt.strftime('%Y-%m-%d %I:%M %p')
        
        return Response(data)


class DeleteReminderView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, telegram_id, reminder_id):
        try:
            reminder = Reminder.objects.get(id=reminder_id, user__telegram_id=telegram_id)
            reminder.delete()
            return Response({'success': True}, status=200)
        except Reminder.DoesNotExist:
            return Response({'error': 'Reminder not found'}, status=404)


class ToggleTimeFormatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, telegram_id):
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
            user.time_format_24h = not user.time_format_24h
            user.save()

            return Response({
                'success': True,
                'time_format_24h': user.time_format_24h
            })
        except TelegramUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        
class MarkReminderSentView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, reminder_id):
        try:
            reminder = Reminder.objects.get(id=reminder_id)
            reminder.is_sent = True
            reminder.save()
            return Response({'success': True}, status=200)
        except Reminder.DoesNotExist:
            return Response({'error': 'Reminder not found'}, status=404)                        


class DueRemindersView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, telegram_id):
        now = datetime.datetime.now()
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
        except TelegramUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        due_reminders = Reminder.objects.filter(
            remind_at__lte=now,
            is_sent=False,
            user=user
        )
        serializer = ReminderWithUserSerializer(due_reminders, many=True)
        return Response(serializer.data)
