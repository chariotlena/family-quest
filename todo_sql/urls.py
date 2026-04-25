from django.urls import path
from . import views
from .views import TaskCreateView, RewardShopView, PurchaseRewardView, RewardCreateView, RewardDeleteView, TaskUpdateView, RewardUpdateView
from django.contrib.auth import views as auth_views
from .forms import RussianLoginForm


urlpatterns = [
    path('', views.TaskListView.as_view(), name='index'),
    path('create/', TaskCreateView.as_view(), name='create_task'),
    path('delete/<int:task_id>/', views.TaskDeleteView.as_view(), name='delete'),
    path('toggle/<int:task_id>/', views.TaskToggleView.as_view(), name='toggle'),
    path('rewards/', RewardShopView.as_view(), name='rewards_shop'),
    path('rewards/buy/', PurchaseRewardView.as_view(), name='purchase_reward'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=RussianLoginForm), name='login'),
    path('rewards/add/', RewardCreateView.as_view(), name='reward_create'),
    path('rewards/delete/<int:reward_id>/', RewardDeleteView.as_view(), name='delete_reward'),
    path('task/<int:task_id>/edit/', TaskUpdateView.as_view(), name='edit_task'),
    path('rewards/<int:reward_id>/edit/', RewardUpdateView.as_view(), name='edit_reward'),
]