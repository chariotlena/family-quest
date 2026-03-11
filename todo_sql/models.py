from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

class Family(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название семьи")
    invite_code = models.CharField(max_length=10, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')

    def __str__(self):
        return f"Профиль: {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class Task(models.Model):
    title = models.CharField('Название квеста', max_length=100)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField('Награда (XP)', default=10)


    def __str__(self):
        return f'{self.title} ({self.points} XP)'

    class Meta:
        verbose_name = 'Квест'
        verbose_name_plural = 'Квесты'
        ordering = ['-created_at']

class Reward(models.Model):
    name = models.CharField('Название награды', max_length=100)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField('Описание', blank=True)
    cost = models.IntegerField('Стоимость (XP)', default=100)
    is_active = models.BooleanField('Активна', default=True)

    def __str__(self):
        return f'{self.name} ({self.cost} XP)'

    class Meta:
        verbose_name = 'Награда'
        verbose_name_plural = 'Награды'

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Покупатель')
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, verbose_name='Купленная награда')
    cost_at_purchase = models.IntegerField('Стоимость (XP)', default=100)
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время покупки')


    def __str__(self):
        return f'{self.user.username} купил {self.reward.name} за {self.cost_at_purchase} XP'

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-purchased_at']


class TaskCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Выполненный квест')
    completion_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата выполнения')
    points_earned = models.IntegerField('Заработано XP', default=0) # Сохраняем очки на момент выполнения

    def save(self, *args, **kwargs):
        if not self.points_earned and self.task: # Если очки не заданы, берем их из задачи
            self.points_earned = self.task.points
        super().save(*args, **kwargs)

    def __str__(self):
        task_title = self.task.title if self.task else "Удаленный квест"
        return f'{self.user.username} выполнил "{task_title}" ({self.points_earned} XP)'

    class Meta:
        verbose_name = 'Выполнение квеста'
        verbose_name_plural = 'Выполнения квестов'
        ordering = ['-completion_date']

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username}: {self.text[:20]}'