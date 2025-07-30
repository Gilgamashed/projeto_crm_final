from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

from projeto_crm_final.models import Integrantes


class AdminRequiredMixin:
    """Mixin para verificar se o usuário autenticado tem perfil de ADMIN"""

    def dispatch(self, request, *args, **kwargs):
        usuario = Integrantes.objects.get(user=self.request.user)
        is_authenticated = self.request.user.is_authenticated
        admin = Integrantes.objects.filter(user=self.request.user).exists() if is_authenticated and usuario.role == 'ADMIN' else False
        if not admin:
            messages.error(self.request, "Apenas administradores podem ter acesso à este canal.")
            return redirect('home')
        request.admin_logado = admin
        return super().dispatch(request, *args, **kwargs)


class LeadRequiredMixin(UserPassesTestMixin):
    """Mixin para permitir criação de projetos apenas por LEADS ou ADMIN"""
    permission_denied_message = "Apenas líderes de equipe e administradores podem criar projetos"
    redirect_url = 'projetos-list'

    def test_func(self):
        # Só prossegue se usuario estiver logado
        if not self.request.user.is_authenticated:
            return redirect('login')

        try:
            integrante = Integrantes.objects.get(user=self.request.user)
            return integrante.role in ['ADMIN', 'LEAD']

        except Integrantes.DoesNotExist:
            return False