from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Integrantes, Projetos, Tarefas, Equipes, RelatorioProjeto, RelatorioTarefa


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
#---------------------------------------------------------------------------------------

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Integrantes
        fields = ['nome', 'sobrenome', 'telefone', 'cargo']
        labels = {
            'nome': 'Nome',
            'sobrenome': 'Sobrenome',
            'telefone': 'Telefone',
            'cargo': 'Cargo'
        }
        widgets = {
            'telefone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'cargo': forms.TextInput(attrs={'placeholder': 'Seu cargo na organização'})
        }


class CredentialsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Nome de Usuário',
            'email': 'Endereço de Email'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Seu identificador único no sistema"
        self.fields['email'].help_text = "Endereço para notificações e recuperação de senha"

# ---------------------------------------------------------------------------------------
class EquipesForm(forms.ModelForm):
    class Meta:
        model = Equipes
        fields = ['name', 'descricao']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da equipe'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Breve descrição da equipe',
                'rows': 4
            }),
        }

        #O lider não é necessario pq vem da view
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['leader'] = forms.ModelChoiceField(
            queryset=Integrantes.objects.all(),
            required=False,
            widget=forms.HiddenInput()
        )

        self.fields['membros'] = forms.ModelMultipleChoiceField(
            queryset=Integrantes.objects.all(),
            required=False,
            widget=forms.MultipleHiddenInput()
        )

    def clean(self):
        cleaned_data = super().clean()
        # Estão na view mas coloquei aqui pra prevenir erros de validação
        cleaned_data['leader'] = self.request.user.integrantes
        cleaned_data['membros'] = [self.request.user.integrantes]
        return cleaned_data


class ProjetosForm(forms.ModelForm):
    class Meta:
        model = Projetos
        fields = ['name', 'descricao', 'categoria', 'prioridade', 'prazofinal',]
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nome do projeto'}),
                   'descricao': forms.Textarea(attrs={'class': 'form-control'}),
                   'categoria': forms.Select(attrs={'class': 'form-control'}),
                   'prioridade': forms.Select(attrs={'class': 'form-control'}),
                   'prazofinal': forms.DateInput(attrs={
                       'class':'form-control',
                       'type':'date',
                       'help_text':'Selecione uma data futura'})
                   }
        labels = {'name' : 'Nome do projeto*',
                  'descricao' : 'Descrição do projeto',
                  'categoria' : 'Categoria',
                  'prioridade' : 'Prioridade*',
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


class RelatorioForm(forms.ModelForm):
    class Meta:
        model = RelatorioProjeto
        fields = ['arquivo']
        widgets = {
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    def clean_arquivo(self):
        file = self.cleaned_data.get('arquivo')
        if file:
            if file.size > 20 * 1024 * 1024:
                raise ValidationError("O arquivo é muito grande (máx. 20MB)")
            # Validar extensao?

        return file

class TarefasForm(forms.ModelForm):
    responsavel = forms.ModelChoiceField(
        queryset=Integrantes.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Responsável'
    )
    class Meta:
        model = Tarefas
        fields = ['name', 'descricao', 'responsavel', 'prioridade', 'prazofinal']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição objetiva da tarefa e suas atribuições',
                'rows': 3
            }),

            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'prazofinal': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {'name' : 'Nome da tarefa*',
                  'descricao' : 'Descrição da tarefa',
                  'responsavel' : 'Responsavel',
                  'prioridade' : 'Prioridade*',
                  'prazofinal' : 'Prazo Final*',
                  'projetoparent': ''}

    def __init__(self, *args, **kwargs):
        self.projeto = kwargs.pop('projetoparent', None)
        super().__init__(*args, **kwargs)

        self.fields['responsavel'].required = False
        self.fields['responsavel'].help_text = "Deixe em branco para não atribuir a ninguém"

        if self.projeto:

            # Filter team members
            if self.projeto.equipe:
                self.fields['responsavel'].queryset = self.projeto.equipe.membros.all()
            else:
                self.fields['responsavel'].queryset = Integrantes.objects.none()
                self.fields['responsavel'].help_text = "O projeto não tem uma equipe atribuída"

    def clean(self):
        cleaned_data = super().clean()
        if self.projeto and self.projeto.equipe:
            responsavel = cleaned_data.get('responsavel')

            # responsavel precisa ser integrante da equipe
            if responsavel and responsavel.equipe != self.projeto.equipe:
                raise ValidationError("O responsável deve pertencer à equipe designada do projeto.")

        return cleaned_data

class RelatorioTarefaForm(forms.ModelForm):
    class Meta:
        model = RelatorioTarefa
        fields = ['descricao', 'arquivo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
        }


