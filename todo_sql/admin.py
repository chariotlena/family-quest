from django.contrib import admin
from .models import Task, Reward, Transaction

# Register your models here.
admin.site.register(Task)
admin.site.register(Reward)
admin.site.register(Transaction)