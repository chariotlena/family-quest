from django import forms
from .models import Task
from django.contrib.auth.forms import UserCreationForm
from .models import ChatMessage


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'points']


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