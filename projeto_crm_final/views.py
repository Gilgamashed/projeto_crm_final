from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView

from projeto_crm_final.forms import SignupForm
from projeto_crm_final.models import Integrantes


class HomeView(TemplateView):
    template_name = "projeto_crm_final/home.html"

class SignUpView(CreateView):
    model = User
    form_class = SignupForm
    template_name = "account/signup.html"
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        Integrantes.objects.create(
            username=self.object,
            first_name= form.cleaned_data.get('first_name'),
            last_name= form.cleaned_data.get('last_name'),
            telefone= form.cleaned_data.get('telefone'),
        )
        login(self.request, self.object)
        return response

class PassResetView(TemplateView):
    template_name = "account/password_reset.html"

class DashboardView(TemplateView):
    model= Integrantes
    template_name = "projeto_crm_final/dashboard.html"
    context_object_name= 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        context['is_admin'] = Integrantes.objects.filter(username=self.request.user).exists() if is_authenticated else False

# Create your views here.
