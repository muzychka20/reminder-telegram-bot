from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, default=0)
    name = models.CharField(max_length=255)
    time_format_24h = models.BooleanField(default=True)


class Reminder(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    text = models.TextField()
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({self.remind_at})"
