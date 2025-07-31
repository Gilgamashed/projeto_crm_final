from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, ListView, DeleteView, UpdateView

from projeto_crm_final.constants import HIERARCH, CATEGORIA
from projeto_crm_final.forms import SignupForm, ProjetosForm
from projeto_crm_final.mixins import AdminRequiredMixin, LeadRequiredMixin, ProjetoOwnerMixin
from projeto_crm_final.models import Integrantes, Projetos


class HomeView(TemplateView):
    template_name = "projeto_crm_final/home.html"

class SignUpView(CreateView):
    model = User
    form_class = SignupForm
    template_name = "account/signup.html"
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

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


