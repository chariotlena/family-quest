from django.urls import path
from . import views
from .views import TaskCreateView, RewardShopView, PurchaseRewardView


urlpatterns = [
    path('', views.TaskListView.as_view(), name='index'),
    path('create/', TaskCreateView.as_view(), name='create_task'),
    path('delete/<int:task_id>/', views.TaskDeleteView.as_view(), name='delete'),
    path('toggle/<int:task_id>/', views.TaskToggleView.as_view(), name='toggle'),
    path('rewards/', RewardShopView.as_view(), name='rewards_shop'),
    path('rewards/buy/', PurchaseRewardView.as_view(), name='purchase_reward'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('chat/', views.ChatView.as_view(), name='chat'),
]