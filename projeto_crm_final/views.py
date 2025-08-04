from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import logger, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, ListView, DeleteView, UpdateView

from projeto_crm_final.constants import HIERARCH, CATEGORIA
from projeto_crm_final.forms import SignupForm, ProjetosForm, EquipesForm, ProfileForm, CredentialsForm
from projeto_crm_final.mixins import AdminRequiredMixin, LeadRequiredMixin, ProjetoOwnerMixin
from projeto_crm_final.models import Integrantes, Projetos, Tarefas, Equipes


class HomeView(TemplateView):
    template_name = "projeto_crm_final/home.html"

# ---------- User e autenticação

class SignUpView(CreateView):
    model = User
    form_class = SignupForm
    template_name = "account/signup.html"
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


@login_required
def edit_profile(request):
    # Editar profile de usuário
    profile = request.user.integrantes

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('home')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'account/user_detail_edit.html', {'form': form})


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user

        # o usuario tem q ser deslogado pra evitar bugs
        logout(request)

        try:
            # deletar ambos Integrantes e User
            user.delete()
            messages.success(request, "Sua conta foi excluída permanentemente.")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao excluir sua conta: {str(e)}")
            return redirect('profile')

    return redirect('profile')


@login_required
def edit_account_info(request):
    user = request.user

    if request.method == 'POST':
        form = CredentialsForm(request.POST, instance=user)
        if form.is_valid():
            # Mudando username?
            new_username = form.cleaned_data['username']
            if new_username != user.username:
                # Está disponível?
                if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    messages.error(request, "Este nome de usuário já está em uso.")
                    return render(request, 'account/user_login_edit.html', {'form': form})

            #Salva
            form.save()
            messages.success(request, "Informações da conta atualizadas com sucesso!")
            return redirect('home')
    else:
        form = CredentialsForm(instance=user)

    return render(request, 'account/user_login_edit.html', {
        'form': form,
        'password_form': PasswordChangeForm(user)
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)       #form do Django
        if form.is_valid():
            user = form.save()
            # Previne logout
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso!")
            return redirect('account_login_info_edit')
        else:
            # Se houver erros, mostra a página com erros
            messages.error(request, "Por favor, corrija os erros abaixo.")
            return render(request, 'account/user_login_edit.html', {
                'form': CredentialsForm(instance=request.user),
                'password_form': form
            })
    return redirect('account_info_edit')


class PassResetView(TemplateView):
    template_name = "account/password_reset.html"

class DashboardView(LoginRequiredMixin, TemplateView):
    model= Integrantes
    template_name = "projeto_crm_final/dashboard.html"
    context_object_name= 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        usuario = Integrantes.objects.get(user=self.request.user)
        context['is_admin'] = Integrantes.objects.filter(user=self.request.user).exists() if is_authenticated and usuario.role == 'ADMIN' else False

        return context


#---Integrantes

class IntegrantesListaView(LoginRequiredMixin, ListView):
    model = Integrantes
    template_name = "admin/integ_list.html"
    context_object_name = 'integrantes'


class IntegrantesGetView(LoginRequiredMixin, DetailView):
    model = Integrantes
    template_name = "account/user_detail.html"
    context_object_name = "perfil"
    pk_url_kwarg = "person_id"

class UpdateRoleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        new_role = "ADMIN"
        user_id = request.POST.get('user_id')

        try:
            integrante = Integrantes.objects.get(person_id=user_id)
            integrante.role = new_role
            integrante.save()
            return JsonResponse({'status': 'success', 'new_role': integrante.get_role_display()})
        except Integrantes.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)


#--------------- EQUIPES

class EquipesView(LoginRequiredMixin, ListView):
    model = Equipes
    template_name = 'projeto_crm_final/equipes_list.html'
    context_object_name = 'equipes'


class EquipesCreateView(LoginRequiredMixin, CreateView):
    model = Equipes
    form_class = EquipesForm
    template_name = 'projeto_crm_final/equipes_form.html'
    success_url = reverse_lazy('equipes_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        try:
            integrante = self.request.user.integrantes   #instancia o criador
            form.instance.leader = integrante   #adiciona criador como lider da equipe
            team = form.save()                  #salva antes pra não bugar o relacionamento entre models
            team.membros.add(integrante)        #adiciona criador aos membros

            integrante.role = 'LEAD'            #no perfil no criador, bota seu role como LEAD
            integrante.equipe = team            #boa sua equipe como a recem criada
            integrante.save()                   #salva o perfil

            messages.success(self.request, "Equipe criada com sucesso!")
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f"Erro ao criar equipe: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        # debugggg
        logger.error(f"Form invalid: {form.errors}")
        return super().form_invalid(form)


class EquipesUpdateView(LoginRequiredMixin, LeadRequiredMixin, UpdateView):
    model = Equipes
    form_class = EquipesForm
    template_name = 'projeto_crm_final/equipes_form.html'

    #Uau! reverse NOT lazy
    def get_success_url(self):
        return reverse('equipes_detail', kwargs={'equipe_id': self.object.pk})

    def get_form_kwargs(self):
        """pros queries de membros(??)"""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        # permissão para leads e admin
        equipe = self.get_object()
        if request.user != equipe.leader.user and request.user.integrantes.role != 'ADMIN':
            messages.error(request, "Você não tem permissão para editar esta equipe.")
            return redirect('equipes_detail', equipe_id=equipe.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            messages.success(self.request, "Equipe atualizada com sucesso!")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar equipe: {str(e)}")
            return self.form_invalid(form)


class EquipesGetView(LoginRequiredMixin, DetailView):
    model = Equipes
    template_name = "projeto_crm_final/equipes_detail.html"
    context_object_name = "equipe"
    pk_url_kwarg = "equipe_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipe = self.get_object()

        # Projetos ativos nesta equipe
        context['active_projeto'] = Projetos.objects.filter(
            equipe=equipe,
            status='active'
        ).first()

        # Projetos disponíveis
        context['available_projetos'] = Projetos.objects.filter(
            status='active'
        ).filter(
            models.Q(equipe__isnull=True) | models.Q(equipe=equipe)
        ).exclude(pk=context['active_projeto'].pk if context['active_projeto'] else None)

        return context

@login_required
def assign_project(request, equipe_id):
    equipe = get_object_or_404(Equipes, pk=equipe_id)

    # Usuário é lider desta equipe?
    if request.user != equipe.leader.user:
        messages.error(request, "Apenas o líder da equipe pode selecionar projetos.")
        return redirect('equipes_detail', equipe_id=equipe_id)

    if request.method == 'POST':
        projeto_id = request.POST.get('projeto_id')
        if projeto_id:
            projeto = get_object_or_404(Projetos, pk=projeto_id)

            try:
                existing_active = Projetos.objects.filter(
                    equipe = equipe,
                    status = 'active'
                ).first()

                if existing_active:
                    existing_active.equipe = None
                    existing_active.save()

                projeto.equipe = equipe
                projeto.save()
                messages.success(request, f"Projeto '{projeto.name}' atribuído à equipe!")
            except ValidationError as e:
                messages.error(request, e.message)
        else:
            messages.error(request, "Selecione um projeto válido.")

    return redirect('equipes_detail', equipe_id=equipe_id)

@login_required
def remove_project(request, equipe_id):
    equipe = get_object_or_404(Equipes, pk=equipe_id)

    if request.user != equipe.leader.user:
        messages.error(request, "Apenas o líder da equipe pode remover projetos.")
        return redirect('equipes_detail', equipe_id=equipe_id)

    if request.method == 'POST':
        projeto_id = request.POST.get('projeto_id')
        if projeto_id:
            projeto = get_object_or_404(Projetos, pk=projeto_id)
            projeto.equipe = None
            projeto.save()
            messages.success(request, f"Projeto '{projeto.name}' removido da equipe.")

    return redirect('equipes_detail', equipe_id=equipe_id)


class EquipesDeleteView(LoginRequiredMixin, LeadRequiredMixin, DeleteView):
    model = Equipes
    template_name = 'projeto_crm_final/equipes_confirm_del.html'
    success_url = reverse_lazy('equipes_list')

    def dispatch(self, request, *args, **kwargs):
        # permissao para lider da equipe e admin
        equipe = self.get_object()
        if request.user != equipe.leader.user and request.user.integrantes.role != 'ADMIN':
            messages.error(request, "Você não tem permissão para excluir esta equipe.")
            return redirect('equipes_detail', equipe_id=equipe.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # projetos desta equipe serão liberados
        Projetos.objects.filter(equipe=self.object).update(equipe=None)

        # membros desta equipe serão liberados
        Integrantes.objects.filter(equipe=self.object).update(equipe=None)

        messages.success(self.request, f"A equipe '{self.object.name}' foi excluída com sucesso!")
        return super().form_valid(form)


#--------------- PROJETOS

class ProjetosView(LoginRequiredMixin, ListView):
    model= Projetos
    template_name='projeto_crm_final/projetos_list.html'
    context_object_name= 'projetos'
    paginate_by = 12

    def get_queryset(self):
        status = self.request.GET.get('status')
        categoria = self.request.GET.get('categoria')
        queryset = Projetos.objects.all()

        if status:
            queryset = queryset.filter(status=status)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Checagem para criação de novos projetos
        context['can_create'] = False
        if self.request.user.is_authenticated:
            try:
                integrante = Integrantes.objects.get(user=self.request.user)
                context['can_create'] = integrante.role in ['ADMIN', 'LEAD']
            except Integrantes.DoesNotExist:
                pass

        context['categorias'] = CATEGORIA

        context['current_status'] = self.request.GET.get('status', '')
        context['current_categoria'] = self.request.GET.get('categoria', '')

        return context

class ProjetosCreateView(LoginRequiredMixin, LeadRequiredMixin, CreateView):
    model = Projetos
    form_class = ProjetosForm
    template_name = 'projeto_crm_final/projetos_form.html'
    success_url = reverse_lazy('projetos_list')

    def form_valid(self, form):                    #associa o projeto ao seu criador?
        integrante = Integrantes.objects.get(user=self.request.user)
        form.instance.criador = integrante
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProjetosUpdateView(LoginRequiredMixin, LeadRequiredMixin, ProjetoOwnerMixin, UpdateView):
    model = Projetos
    form_class = ProjetosForm
    template_name = 'projeto_crm_final/projetos_form.html'
    success_url = reverse_lazy('projetos_list')

class ProjetosGetView(LoginRequiredMixin, DetailView):
    model = Projetos
    template_name = "projeto_crm_final/projetos_detail.html"
    context_object_name = "projeto"
    pk_url_kwarg = "projeto_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Checagem para criação de novos projetos
        context['can_create'] = False
        if self.request.user.is_authenticated:
            try:
                integrante = Integrantes.objects.get(user=self.request.user)
                context['can_create'] = integrante.role in ['ADMIN', 'LEAD']
            except Integrantes.DoesNotExist:
                pass
        return context

class ProjetosDeleteView(LoginRequiredMixin,LeadRequiredMixin, ProjetoOwnerMixin, DeleteView):
    model = Projetos
    template_name = 'projeto_crm_final/projetos_confirm_del.html'
    success_url = reverse_lazy('projetos_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Projeto cancelado com sucesso!")
        return super().delete(request, *args, **kwargs)



#--------------- TAREFAS
"""
class TarefasView(LoginRequiredMixin, ListView):
    model= Tarefas
    template_name=
    context_object_name= 'tarefas'

class TarefasCreateView(LoginRequiredMixin, LeadRequiredMixin, CreateView):
    model = Tarefas
    form_class = TarefasForm
    template_name = 'projeto_crm_final/tarefas_form.html'
    success_url = reverse_lazy('')

class TarefasUpdateView(LoginRequiredMixin, LeadRequiredMixin, ProjetoOwnerMixin, UpdateView):
    model = Tarefas
    form_class = TarefasForm
    template_name = 'projeto_crm_final/tarefas_form.html'
    success_url = reverse_lazy('')

class TarefasGetView(LoginRequiredMixin, DetailView):
    model = Tarefas
    template_name = "projeto_crm_final/tarefas_detail.html"
    context_object_name = "tarefa"
    pk_url_kwarg = "tarefa_id"

class TarefasDeleteView(LoginRequiredMixin,LeadRequiredMixin, ProjetoOwnerMixin, DeleteView):
    model = Tarefas
    template_name = 'projeto_crm_final/tarefas_confirm_del.html'
    success_url = reverse_lazy('')

"""