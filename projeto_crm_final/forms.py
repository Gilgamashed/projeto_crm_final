from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from projeto_crm_final.models import Integrantes


class SignupForm(UserCreationForm):
    nome = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nome*',
        error_messages={
            'required': 'Por favor, insira seu nome'
        }
    )
    sobrenome = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Sobrenome*',
        error_messages={
            'required': 'Por favor, insira seu sobrenome'
        }
    )
    email = forms.EmailField(
        label='E-mail*',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Por favor, insira um e-mail valido'
        }
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Telefone'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Usuário*',
        }

        help_texts = {
            'username': 'Obrigatório. 20 caracteres ou menos. Letras, números e @/./+/-/_ apenas.',
            'email': 'Por favor, insira um e-mail válido.'
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.nome = self.cleaned_data['nome']
        user.sobrenome = self.cleaned_data['sobrenome']
        if commit:
            user.save()


        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].label = 'Senha*'
        self.fields['password2'].label = 'Confirme a Senha*'

        self.fields['password1'].help_text = (
            "Sua senha deve conter pelo menos 8 caracteres. "
            "Evite usar informações pessoais."
        )
        self.fields['password2'].help_text = "Repita a senha para verificação."
