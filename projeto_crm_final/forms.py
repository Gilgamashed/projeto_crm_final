from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Integrantes, Projetos, Tarefas, Equipes


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

    #def save(self, commit=True):
    #    user = super().save(commit=False)
    #    user.nome = self.cleaned_data['nome']
    #    user.sobrenome = self.cleaned_data['sobrenome']
    #    if commit:
    #        user.save()
    #    return user

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['nome']
        user.last_name = self.cleaned_data['sobrenome']
        user.save()  # Save user first

        # models User e Integrantes são diferentes - abaixo ele passa a informação do User para o Integrantes
        Integrantes.objects.create(
            user=user,
            nome=self.cleaned_data['nome'],
            sobrenome=self.cleaned_data['sobrenome'],
            telefone=self.cleaned_data.get('telefone','')
        )
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


class EquipesForm(forms.ModelForm):
    class Meta:
        model = Equipes
        fields = ['name', 'descricao', 'leader']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nome da equipe'}),
                   'descricao': forms.Textarea(attrs={
                       'class': 'form-control', 'placeholder':'Breve descrição da equipe'}),
                        'leader': forms.HiddenInput(),
                   }


class ProjetosForm(forms.ModelForm):
    class Meta:
        model = Projetos
        fields = ['name', 'descricao', 'categoria', 'prazofinal',]
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nome do projeto'}),
                   'descricao': forms.Textarea(attrs={'class': 'form-control'}),
                   'categoria': forms.Select(attrs={'class': 'form-control'}),
                   'prazofinal': forms.DateInput(attrs={
                       'class':'form-control',
                       'type':'date',
                       'help_text':'Selecione uma data futura'})
                   }
        labels = {'name' : 'Nome do projeto*',
                  'descricao' : 'Descrição do projeto',
                  'categoria' : 'Categoria',
                  'prazofinal' : 'Prazo Final*'}

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.instance and self.instance.pk:
            if Projetos.objects.filter(name=name, status="active").exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Um projeto com este nome já está ativo.")
        else:
            if Projetos.objects.filter(name=name, status="active").exists():
                raise forms.ValidationError("Um projeto com este nome já está ativo.")
        return name

    def clean_prazofinal(self):
        date = self.cleaned_data['prazofinal']
        if date <= date.today():
            raise forms.ValidationError("Prazo deve ser uma data futura!")
        return date


class TarefasForm(forms.ModelForm):
    class Meta:
        model = Tarefas
        fields = ['tarefa', 'descricao', 'prazofinal', 'prioridade']
        widgets = {}
