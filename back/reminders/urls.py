from django.urls import path
from .views import RegisterUserView, CreateReminderView, ListRemindersView, DeleteReminderView, ToggleTimeFormatView, MarkReminderSentView, DueRemindersView


urlpatterns = [
    path('register/', RegisterUserView.as_view()),
    path('reminders/create/', CreateReminderView.as_view()),
    path('reminders/<int:telegram_id>/', ListRemindersView.as_view()),
    path('reminders/<int:telegram_id>/<int:reminder_id>/delete/', DeleteReminderView.as_view()),
    path('toggle-time-format/<int:telegram_id>/', ToggleTimeFormatView.as_view()),
    path('reminders/mark-sent/<int:reminder_id>/', MarkReminderSentView.as_view()),
    path('reminders/due/<int:telegram_id>/', DueRemindersView.as_view()),
]