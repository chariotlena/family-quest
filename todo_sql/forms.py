from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Task, ChatMessage, Reward


class RussianLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'points']


class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields =['name', 'description', 'cost']


class EmailUserCreationForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)

    class Meta(UserCreationForm.Meta):
        model = UserCreationForm.Meta.model
        fields = UserCreationForm.Meta.fields + ('email',)


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите что-нибудь семье...',
                'autocomplete': 'off'
            }),
        }


class FamilySignUpForm(EmailUserCreationForm):
    family_name = forms.CharField(max_length=100, required=False, label="Название новой семьи")
    invite_code = forms.CharField(max_length=10, required=False, label="Или код приглашения")

    def clean(self):
        cleaned_data = super().clean()
        family_name = cleaned_data.get('family_name')
        invite_code = cleaned_data.get('invite_code')

        if not family_name and not invite_code:
            raise forms.ValidationError(
                "Укажите название новой семьи или код приглашения существующей. "
                "Без семьи вам не будет доступен ни один раздел сайта."
            )

        return cleaned_data

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['username'].help_text = 'Не более 150 символов. Буквы, цифры и символы @/./+/-/_'

        self.fields['email'].label = 'Электронная почта'

        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].help_text = '''
            Пароль не должен совпадать с личными данными.
            Минимум 8 символов.
            Пароль не должен быть слишком простым.
            Пароль не может состоять только из цифр.
        '''

        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password2'].help_text = 'Введите пароль ещё раз для проверки.'