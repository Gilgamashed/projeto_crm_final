import csv

import cloudinary
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import logger, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, ListView, DeleteView, UpdateView

from projeto_crm_final.constants import CATEGORIA, PRIORIDADE, STATUS
from projeto_crm_final.forms import SignupForm, ProjetosForm, EquipesForm, ProfileForm, CredentialsForm, RelatorioForm, \
    TarefasForm, RelatorioTarefaForm
from projeto_crm_final.mixins import LeadRequiredMixin, ProjetoOwnerMixin
from projeto_crm_final.models import Integrantes, Projetos, Tarefas, Equipes


class HomeView(TemplateView):
    template_name = "projeto_crm_final/home.html"

# ---------- User e autenticação

class SignUpView(CreateView):
    model = User
    form_class = SignupForm
    template_name = "account/signup.html"
    success_url = reverse_lazy('dashboard')

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

#------------ Dashboard -----------
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'projeto_crm_final/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            integrante = Integrantes.objects.get(user=user)
            context['integrante'] = integrante

            if integrante.equipe:
                context['equipe'] = integrante.equipe

                active_projeto = Projetos.objects.filter(       #pega projeto ativo
                    equipe=integrante.equipe,
                    status='active'
                ).first()

                if active_projeto:
                    context['active_projeto'] = active_projeto
                    context['todo_tasks'] = Tarefas.objects.filter(
                        projetoparent=active_projeto,
                        status='todo'
                    )
                    context['doing_tasks'] = Tarefas.objects.filter(
                        projetoparent=active_projeto,
                        status='doing'
                    )
                    context['done_tasks'] = Tarefas.objects.filter(
                        projetoparent=active_projeto,
                        status='done'
                    )
                else:
                    context['active_projeto'] = None
            else:
                context['no_team'] = True

        except Integrantes.DoesNotExist:
            context['no_profile'] = True

        return context

# ------- Tarefas - porque deixei aqui e nao no fim?! ----------
class TarefasAssign(View):
    def post(self, request, task_id):
        integrante = Integrantes.objects.get(user=request.user)
        task = Tarefas.objects.get(id=task_id)
        task.responsavel = integrante
        task.status = 'doing'
        task.save()
        return redirect('dashboard')


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = self.get_object()

        if perfil.equipe:
            context['active_project'] = Projetos.objects.filter(
                equipe=perfil.equipe,
                status='active'
            ).first()
        else:
            context['active_project'] = None

        return context

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipes = Equipes.objects.all()

        # pega o time do usuario atual
        user_team = None
        if self.request.user.is_authenticated and hasattr(self.request.user, 'integrantes'):
            user_team = self.request.user.integrantes.equipe

        context['equipes'] = equipes
        context['user_team'] = user_team

        return context


class EquipesCreateView(LoginRequiredMixin, CreateView):
    model = Equipes
    form_class = EquipesForm
    template_name = 'projeto_crm_final/equipes_form.html'
    success_url = reverse_lazy('equipes_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        # Qm já tem uma equipe nao pode criar uma nova
        if hasattr(request.user, 'integrantes') and request.user.integrantes.equipe:
            messages.warning(
                request,
                "Você já faz parte de uma equipe. Saia da sua equipe atual para criar uma nova."
            )
            return redirect('equipes_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            integrante = self.request.user.integrantes   #instancia o criador
            if integrante.equipe:                       #garante que usuario nao tem time
                messages.error(
                    self.request,
                    "Você já faz parte de uma equipe. Saia da sua equipe atual para criar uma nova."
                )
                return redirect('equipes_list')
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


class EquipesLeaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        integrante = request.user.integrantes

        #Lider deve passar liderança antes de sair
        if integrante.role == 'LEAD':
            messages.error(
                request,
                "Você é o líder desta equipe. Transfira a liderança antes de sair."
            )
            return redirect('equipes_detail', equipe_id=integrante.equipe.id)

        #sai do grupo
        team = integrante.equipe
        team.membros.remove(integrante)
        integrante.equipe = None
        integrante.role = 'MEMBER'  # volta a seer membro
        integrante.save()

        messages.success(request, "Você saiu da equipe com sucesso!")
        return redirect('equipes_list')


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

        #membros disponíveis para entrar na eequipe
        current_members_ids = equipe.membros.all().values_list('person_id', flat=True)
        context['available_integrantes'] = Integrantes.objects.exclude(
            person_id__in=current_members_ids
        ).filter(
            models.Q(equipe__isnull=True) | models.Q(equipe=equipe)
        ).distinct()

        return context

    def post(self, request, *args, **kwargs):
        equipe = self.get_object()
        active_projeto = equipe.projetos_set.filter(status='active').first()

        if not active_projeto:
            messages.error(request,"Nenhum projeto ativo sendo trabalhado por essa equipe")
            return redirect('equipes_detail', equipe_id=equipe.id)

        form = RelatorioForm(request.POST, request.FILES)

        if form.is_valid():
            # Salva o relatório
            relatorio = form.save(commit=False)
            relatorio.projeto = active_projeto
            relatorio.enviado_por = request.user.integrantes
            relatorio.save()

            #Upload pro Cloudinary
            file = relatorio.arquivo
            date_prefix = timezone.now().strftime('%Y_%m_%d')
            filename = f'{date_prefix}_relatorio_{active_projeto.name}'

            upload_result = cloudinary.uploader.upload(
                file=file,
                asset_folder='relatorios',
                public_id=filename,
                override=True,
                resource_type="raw"
            )

            # Atualiza status do Projeto e da equipe
            active_projeto.status = 'done'
            active_projeto.save()

            # Email de todos do time
            team_members = active_projeto.equipe.membros.all()
            emails = [membro.user.email for membro in team_members]

            # Prepara e manda o e-mail
            subject = f'Projeto {active_projeto.name} Concluído'
            message = f'''
            Parabéns à equipe {equipe.name}!
            O projeto "{active_projeto.name}" foi concluído pelo líder da equipe.
            
            Descrição do projeto:
            {active_projeto.descricao}

            Relatório disponível em: {upload_result['secure_url']}
            '''

            email = EmailMessage(
                subject,
                message,
                request.user.email,  # do usuario atual
                emails,  # pra todos os membros da equipe
                [settings.EMAIL_HOST_USER],  # BCC pro system
            )
            email.send()

            messages.success(request, 'Projeto concluído com sucesso e relatório enviado!')
            return redirect('equipes_detail', equipe_id=equipe.id)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

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

    return render(request, 'equipes_detail.html', context)

def equipes_invite(request, equipe_id):
    equipe = get_object_or_404(Equipes, id=equipe_id)

    if request.method == 'POST':
        integrante_id = request.POST.get('integrante_id')

        if not (request.user == equipe.leader.user or request.user.integrantes.role == 'ADMIN'):
            return HttpResponseForbidden("Permissão negada")

        try:
            integrante = Integrantes.objects.get(person_id=integrante_id)
            equipe.add_member(integrante)
            messages.success(request, f"{integrante.nome} foi adicionado à equipe!")
        except Integrantes.DoesNotExist:
            messages.error(request, "Integrante não encontrado")

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
        prioridade = self.request.GET.get('prioridade')
        queryset = Projetos.objects.all()

        #filtro de status
        hoje = timezone.now().date()
        if status == 'active':
            queryset = queryset.filter(status='active')
        elif status == 'canceled':
            queryset = queryset.filter(status='canceled')
        elif status == 'overdue':
            queryset = queryset.filter(
                status='active',
                prazofinal__lt=hoje
            )
        elif status == 'done':
            queryset = queryset.filter(status='done')

        #Filtros adicionais (acumulativos)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if prioridade:
            queryset = queryset.filter(prioridade=prioridade)
        return queryset.order_by('-inicio')

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
        context['prioridades'] = PRIORIDADE

        current_status = self.request.GET.get('status', '')
        current_categoria = self.request.GET.get('categoria', '')
        current_prioridade = self.request.GET.get('prioridade', '')

        context['current_status'] = self.request.GET.get('status', '')
        context['current_categoria'] = self.request.GET.get('categoria', '')
        context['current_prioridade'] = self.request.GET.get('prioridade','')

        # Display pros filtros
        context['current_categoria_display'] = self.get_display_value(CATEGORIA, current_categoria)
        context['current_prioridade_display'] = self.get_display_value(PRIORIDADE, current_prioridade)

        return context

    def get_display_value(self, choices, value):
        """valor de display pros filtros"""
        for key, display in choices:
            if key == value:
                return display
        return ''

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
        projeto = self.get_object()
        context["tarefas"] = None
        context["can_create"] = False
        context["user_is_equipe"] = False

        if self.request.user.is_authenticated:
            integrante = self.request.user.integrantes

            # user é da equipe?
            if projeto.equipe and integrante in projeto.equipe.membros.all():
                context["user_is_equipe"] = True
                context["tarefas"] = projeto.tarefas_do_projeto.all().order_by("prazofinal")

                # checa se usuario pode criar tareefas
                if integrante == projeto.criador or integrante.role == "ADMIN":
                    context["can_create"] = True

            # sempree permite admin ver tarefas mesmo se nao for da equipe
            elif integrante == projeto.criador or integrante.role == "ADMIN":
                context["user_is_equipe"] = True
                context["tarefas"] = projeto.tarefas_do_projeto.all().order_by("prazofinal")
                context["can_create"] = True

        context["PRIORIDADE"] = PRIORIDADE
        return context

class ProjetosDeleteView(LoginRequiredMixin,LeadRequiredMixin, ProjetoOwnerMixin, DeleteView):
    model = Projetos
    template_name = 'projeto_crm_final/projetos_confirm_del.html'
    success_url = reverse_lazy('projetos_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Projeto cancelado com sucesso!")
        return super().delete(request, *args, **kwargs)



#--------------- TAREFAS

class TarefasCreateView(LoginRequiredMixin, CreateView):
    model = Tarefas
    form_class = TarefasForm
    template_name = "projeto_crm_final/projetos_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.projeto = get_object_or_404(Projetos, pk=self.kwargs["projeto_id"])

        # Checa se o projeto está sendo trabalhado por um time
        if not self.projeto.equipe:
            messages.error(request,
            "Projeto não está atribuído a uma equipe. Atribua o projeto a uma equipe antes de criar tarefas.")
            return redirect("projetos_detail", projeto_id=self.projeto.pk)

        # Confere se usuario é parte do time que trabalha com o projeto
        user_team = request.user.integrantes.equipe
        if not user_team or user_team != self.projeto.equipe:
            messages.error(request, "Você não faz parte da equipe deste projeto.")
            return redirect("projetos_detail", projeto_id=self.projeto.pk)

        # Checa se usuario criou a tarefa OU se é ADMIN
        if not (request.user.integrantes == self.projeto.criador or
                request.user.integrantes.role == "ADMIN"):
            messages.error(request, "Você não tem permissão para criar tarefas para este projeto.")
            return redirect("projetos_detail", projeto_id=self.projeto.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["projetoparent"] = self.projeto
        return kwargs

    def form_valid(self, form):
        tarefa = form.save(commit=False)
        tarefa.projetoparent = self.projeto
        tarefa.equipe = self.projeto.equipe
        if tarefa.responsavel:
            tarefa.status = 'doing'
        tarefa.save()
        messages.success(self.request, "Tarefa criada com sucesso!")
        return redirect("projetos_detail", projeto_id=self.projeto.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projeto"] = self.projeto
        context["PRIORIDADE"] = PRIORIDADE
        return context

class TarefasUpdateView(LoginRequiredMixin, UpdateView):
    model = Tarefas
    form_class = TarefasForm
    template_name = "projeto_crm_final/projetos_detail.html"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        self.tarefa = self.get_object()
        self.projeto = self.tarefa.projetoparent
        #permissão especial, igual o view de criar
        if not (request.user.integrantes == self.projeto.criador or request.user.integrantes == self.tarefa.responsavel or request.user.integrantes.role == "ADMIN"):
            messages.error(request, "Você não tem permissão para editar esta tarefa.")
            return redirect("projetos_detail", projeto_id=self.projeto.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["projetoparent"] = self.projeto
        return kwargs

    def form_valid(self, form):
        tarefa = form.save(commit=False)
        if tarefa.responsavel:
            tarefa.status = 'doing'
        else:
            tarefa.status = 'todo'
        tarefa.save()
        messages.success(self.request, "Tarefa atualizada com sucesso!")
        return redirect("projetos_detail", projeto_id=self.projeto.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tarefa"] = self.tarefa
        context["projeto"] = self.projeto
        context["PRIORIDADE"] = PRIORIDADE
        return context

class TarefasDeleteView(LoginRequiredMixin, DeleteView):
    model = Tarefas
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        self.tarefa = self.get_object()
        self.projeto = self.tarefa.projetoparent
        # Permissão
        if not (request.user.integrantes == self.projeto.criador or request.user.integrantes.role == "ADMIN"):
            messages.error(request, "Você não tem permissão para excluir esta tarefa.")
            return redirect("projetos_detail", projeto_id=self.projeto.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Tarefa excluída com sucesso!")
        return reverse("projetos_detail", kwargs={"projeto_id": self.projeto.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tarefa"] = self.tarefa
        context["projeto"] = self.projeto
        return context

        #metodo pro modal funcionar
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return response

class TarefasDetailView(LoginRequiredMixin, DetailView):
    model = Tarefas
    template_name = "projeto_crm_final/tarefas_detail.html"
    context_object_name = "tarefa"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['PRIORIDADE'] = PRIORIDADE
        context['STATUS'] = STATUS
        return context


class TarefasReportView(LoginRequiredMixin, View):
    template_name = 'projeto_crm_final/tarefas_report.html'

    def get(self, request, task_id):
        task = get_object_or_404(Tarefas, id=task_id)

        # Responsavel pela tarefa
        if task.responsavel.user != request.user:
            messages.error(request, "Você não é o responsável por esta tarefa.")
            return redirect('dashboard')

        form = RelatorioTarefaForm()
        return render(request, self.template_name, {
            'task': task,
            'form': form
        })

    def post(self, request, task_id):
        task = get_object_or_404(Tarefas, id=task_id)
        integrante = request.user.integrantes

        # Responsavel pela tarefa de novo!
        if task.responsavel != integrante:
            messages.error(request, "Você não é o responsável por esta tarefa.")
            return redirect('dashboard')

        form = RelatorioTarefaForm(request.POST, request.FILES)

        if form.is_valid():
            # Salva o relatorio
            relatorio = form.save(commit=False)
            relatorio.tarefa = task
            relatorio.enviado_por = integrante
            relatorio.save()

            # Manda pro cloud
            file = relatorio.arquivo
            date_prefix = timezone.now().strftime('%Y_%m_%d')
            filename = f'{date_prefix}_relatorio_{task.id}_{task.name[:20]}'

            try:
                upload_result = cloudinary.uploader.upload(
                    file=file,
                    asset_folder='relatorios_tarefas',
                    public_id=filename,
                    override=True,
                    resource_type="raw"
                )
                # URL
                relatorio.cloudinary_url = upload_result['secure_url']
                relatorio.save()
            except Exception as e:      #debugg
                messages.warning(request, f"Arquivo salvo localmente. Erro no Cloudinary: {str(e)}")

            # Salva
            task.status = 'done'
            task.save()

            # Membros da e quipe
            team_members = task.projetoparent.equipe.membros.all()
            emails = [membro.user.email for membro in team_members if membro.user.email]

            # manda email pra todos
            if emails:
                subject = f'Tarefa Concluída: {task.name}'
                message = f'''
                A tarefa "{task.name}" foi concluída por {integrante.nome}.

                Descrição da tarefa:
                {task.descricao}

                Relatório:
                {relatorio.descricao}

                Arquivo do relatório: {relatorio.arquivo.url}
                '''

                try:
                    email = EmailMessage(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        emails,
                        [settings.EMAIL_HOST_USER],
                    )
                    if hasattr(relatorio, 'cloudinary_url'):
                        email.body += f"\nLink Cloudinary: {relatorio.cloudinary_url}"
                    email.send()
                except Exception as e:
                    messages.warning(request, f"Relatório salvo, mas e-mail não enviado: {str(e)}")

            messages.success(request, 'Tarefa concluída e relatório enviado com sucesso!')
            return redirect('dashboard')

        return render(request, self.template_name, {
            'task': task,
            'form': form
        })

class TarefasExportCSSView(LoginRequiredMixin, LeadRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Checa o projeto ativo do time
        integrante = request.user.integrantes
        if not integrante or not integrante.equipe:
            return HttpResponse("Usuário sem equipe", status=400)

        #Checagem pra ver se a equipe tem projeto ativo
        active_project = Projetos.objects.filter(
            equipe=integrante.equipe,
            status='active'
        ).first()

        if not active_project:
            return HttpResponse("Nenhum projeto ativo", status=400)

        messages.success(self.request, "Download CSV iniciado...")

        # Cria a HttpResponse com header CSV
        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime('%Y_%m_%d')
        filename = f'tarefas_{active_project.name}_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # CSV começa aqui!
        writer = csv.writer(response)

        # Colunas
        writer.writerow([
            'Nome', 'Descrição', 'Status', 'Prioridade',
            'Responsável', 'Data Criação', 'Prazo Final'
        ])

        # Linhas
        tasks = Tarefas.objects.filter(projetoparent=active_project)
        for task in tasks:
            writer.writerow([
                task.name,
                task.descricao,
                task.get_status_display(),
                task.get_prioridade_display(),
                f"{task.responsavel.nome} {task.responsavel.sobrenome}" if task.responsavel else "Não atribuído",
                task.inicio.strftime('%d/%m/%Y %H:%M'),
                task.prazofinal.strftime('%d/%m/%Y') if task.prazofinal else ""
            ])

        # Menssagens
        storage = messages.get_messages(request)
        storage.used = False  #???

        return response
