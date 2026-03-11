from django.shortcuts import render, redirect, get_object_or_404
from .models import Task, Reward, Transaction, TaskCompletion, Family, ChatMessage
from .forms import TaskForm, FamilySignUpForm, ChatMessageForm
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.views.generic import ListView, CreateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime
from django.utils import timezone


def get_user_family(user):
    """Вспомогательная функция: возвращает семью пользователя или None."""
    if hasattr(user, 'profile') and user.profile.family:
        return user.profile.family
    return None


def purge_old_chat_messages(family):
    """Удаляет сообщения семьи старше 7 дней."""
    cutoff = timezone.now() - datetime.timedelta(days=7)
    deleted_count, _ = ChatMessage.objects.filter(
        family=family,
        created_at__lt=cutoff
    ).delete()
    return deleted_count


class TaskListView(ListView):
    """Главная страница: список квестов и таблица лидеров семьи."""
    model = Task
    template_name = 'index.html'
    context_object_name = 'tasks'

    def get_context_data(self, **kwargs):
        """Добавляет в контекст форму, таблицу лидеров и задачи семьи."""
        context = super().get_context_data(**kwargs)
        context['form'] = TaskForm()
        user = self.request.user
        leaderboard = []

        if user.is_authenticated and hasattr(user, 'profile') and user.profile.family:
            user_family = user.profile.family

            family_users = User.objects.filter(profile__family=user_family)

            for u in family_users:
                total_earned_xp = TaskCompletion.objects.filter(user=u).aggregate(Sum('points_earned'))[
                                      'points_earned__sum'] or 0

                total_spent_xp = Transaction.objects.filter(
                    user=u,
                ).aggregate(Sum('cost_at_purchase'))['cost_at_purchase__sum'] or 0

                current_xp_balance = total_earned_xp - total_spent_xp
                leaderboard.append({'name': u.username, 'score': current_xp_balance})

            leaderboard.sort(key=lambda x: x['score'], reverse=True)
            for i, hero in enumerate(leaderboard):
                if i == 0:
                    hero['rank_icon'] = '🥇'
                elif i == 1:
                    hero['rank_icon'] = '🥈'
                elif i == 2:
                    hero['rank_icon'] = '🥉'
                else:
                    hero['rank_icon'] = '👤'

            all_available_tasks = Task.objects.filter(
                Q(family=user_family) | Q(family__isnull=True)
            )

            completed_task_ids = set(TaskCompletion.objects.filter(
                user=user,
                completion_date__date=timezone.now().date()
            ).values_list('task__id', flat=True))

            tasks_for_display = []
            for task in all_available_tasks:
                task.is_completed_by_user = task.id in completed_task_ids
                task.can_be_completed = True
                tasks_for_display.append(task)

            context['tasks'] = tasks_for_display
        else:
            context['tasks'] = []
            leaderboard = []

        context['leaderboard'] = leaderboard
        return context


class RewardShopView(ListView):
    """Магазин наград: показывает награды."""
    model = Reward
    template_name = 'rewards_shop.html'
    context_object_name = 'rewards'

    def get_queryset(self):
        """Фильтрует награды: только своей семьи + общие (family=NULL)."""
        user = self.request.user
        if user.is_authenticated:
            family = get_user_family(user)
            if family:
                return Reward.objects.filter(
                    Q(family=family) | Q(family__isnull=True),
                    is_active=True
                )
        return Reward.objects.none()

    def get_context_data(self, **kwargs):
        """Добавляет в контекст текущий баланс XP."""
        context = super().get_context_data(**kwargs)
        user_xp_balance = 0
        if self.request.user.is_authenticated:
            current_user = self.request.user
            total_earned_xp = TaskCompletion.objects.filter(user=current_user).aggregate(Sum('points_earned'))[
                                  'points_earned__sum'] or 0
            total_spent_xp = Transaction.objects.filter(
                user=current_user,
            ).aggregate(Sum('cost_at_purchase'))['cost_at_purchase__sum'] or 0
            user_xp_balance = total_earned_xp - total_spent_xp

        context['user_xp_balance'] = user_xp_balance
        return context


class PurchaseRewardView(LoginRequiredMixin, View):
    """Покупка награды: списывает XP и создаёт транзакцию."""

    def post(self, request, *args, **kwargs):
        """Проверяет баланс XP и создаёт транзакцию, если средств достаточно."""
        reward = get_object_or_404(Reward, id=request.POST.get('reward_id'))
        current_user = request.user

        total_earned_xp = TaskCompletion.objects.filter(user=current_user).aggregate(Sum('points_earned'))[
                              'points_earned__sum'] or 0
        total_spent_xp = Transaction.objects.filter(
            user=current_user,
        ).aggregate(Sum('cost_at_purchase'))['cost_at_purchase__sum'] or 0
        user_xp_balance = total_earned_xp - total_spent_xp

        if user_xp_balance >= reward.cost:
            Transaction.objects.create(
                user=current_user,
                reward=reward,
                cost_at_purchase=reward.cost,
            )
            messages.success(request, f'Награда "{reward.name}" куплена! Можете ею воспользоваться.')
        else:
            messages.error(request, 'Недостаточно XP.')
        return redirect('rewards_shop')


class TaskCreateView(LoginRequiredMixin, View):
    """Создание нового квеста для семьи текущего пользователя."""

    def post(self, request, *args, **kwargs):
        """Валидирует форму и сохраняет квест, привязав его к семье пользователя."""
        form = TaskForm(request.POST)
        if form.is_valid():
            if hasattr(request.user, 'profile') and request.user.profile.family:
                new_task = form.save(commit=False)
                new_task.family = request.user.profile.family
                new_task.save()
                messages.success(request, f"Квест «{new_task.title}» добавлен!")
            else:
                messages.error(request, "Вы не состоите в семье, чтобы создавать задачи.")
        else:
            messages.error(request, "Ошибка: введите название квеста.")
        return redirect('index')

    def get(self, request, *args, **kwargs):
        """Редиректит на главную при прямом переходе по URL."""
        return redirect('index')


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление квеста. Доступно только членам семьи, которой принадлежит квест."""
    model = Task
    success_url = reverse_lazy('index')
    pk_url_kwarg = 'task_id'

    def get_queryset(self):
        """Ограничивает выборку задачами только своей семьи."""
        family = get_user_family(self.request.user)
        if family is None:
            return self.model.objects.none()
        return self.model.objects.filter(family=family)

    def get(self, request, *args, **kwargs):
        """Удаляет задачу при GET-запросе (переход по ссылке удаления)."""
        messages.warning(request, "Задача удалена.")
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Удаляет задачу при POST-запросе (отправка формы)."""
        messages.warning(request, "Задача удалена.")
        return self.delete(request, *args, **kwargs)


class TaskToggleView(LoginRequiredMixin, View):
    """Отметка квеста выполненным или отмена отметки за сегодня."""

    def get(self, request, *args, **kwargs):
        """Переключает статус выполнения квеста для текущего пользователя на сегодня."""
        family = get_user_family(request.user)
        if family is None:
            messages.error(request, "Вы не состоите в семье.")
            return redirect('index')

        task = get_object_or_404(
            Task,
            Q(id=kwargs['task_id']) & (Q(family=family) | Q(family__isnull=True))
        )

        today_completion = TaskCompletion.objects.filter(
            user=request.user,
            task=task,
            completion_date__date=timezone.now().date()
        ).first()

        if today_completion:
            today_completion.delete()
            messages.info(request, f'Отмена: "{task.title}".')
        else:
            TaskCompletion.objects.create(user=request.user, task=task, points_earned=task.points)
            messages.success(request, f'Выполнено: "{task.title}"! +{task.points} XP.')

        return redirect('index')


class ChatView(LoginRequiredMixin, ListView):
    """Семейный чат: просмотр и отправка сообщений."""
    model = ChatMessage
    template_name = 'chat.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        """Возвращает сообщения только своей семьи."""
        if hasattr(self.request.user, 'profile') and self.request.user.profile.family:
            return ChatMessage.objects.filter(family=self.request.user.profile.family)
        return ChatMessage.objects.none()

    def get(self, request, *args, **kwargs):
        """Редиректит на главную, если у пользователя нет семьи."""
        if get_user_family(request.user) is None:
            messages.error(
                request,
                "У вас нет семьи — чат недоступен. "
                "Создайте семью или вступите в существующую."
            )
            return redirect('index')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Добавляет в контекст пустую форму отправки сообщения."""
        context = super().get_context_data(**kwargs)
        context['form'] = ChatMessageForm()
        return context

    def post(self, request, *args, **kwargs):
        """Сохраняет новое сообщение, привязав его к пользователю и семье."""
        family = get_user_family(request.user)
        if family is None:
            messages.error(request, "Вы не состоите в семье.")
            return redirect('chat')

        form = ChatMessageForm(request.POST)
        if form.is_valid():
            new_message = form.save(commit=False)
            new_message.user = request.user
            new_message.family = family
            new_message.save()
            return redirect('chat')
        return self.get(request, *args, **kwargs)


class SignUpView(CreateView):
    """Регистрация: создаёт пользователя и привязывает его к семье."""
    form_class = FamilySignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        """Создаёт семью по названию или присоединяет по инвайт-коду."""
        response = super().form_valid(form)
        user = self.object
        family_name = form.cleaned_data.get('family_name')
        invite_code = form.cleaned_data.get('invite_code')

        if invite_code:
            family = get_object_or_404(Family, invite_code=invite_code.upper())
            user.profile.family = family
        elif family_name:
            family = Family.objects.create(name=family_name)
            user.profile.family = family

        user.profile.save()
        messages.success(self.request, "Регистрация прошла успешна!")
        return response