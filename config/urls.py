"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.decorators.http import require_POST

from projeto_crm_final.views import SignUpView, HomeView, PassResetView, DashboardView, IntegrantesGetView, \
    UpdateRoleView, IntegrantesListaView, ProjetosCreateView, ProjetosUpdateView, ProjetosView, ProjetosGetView, \
    ProjetosDeleteView, EquipesView, EquipesCreateView, EquipesUpdateView, EquipesGetView, EquipesDeleteView, \
    assign_project, remove_project, edit_profile, delete_account, edit_account_info, change_password, equipes_invite, \
    TarefasCreateView, TarefasUpdateView, TarefasDeleteView, TarefasDetailView, TarefasAssign, TarefasReportView, \
    EquipesLeaveView, TarefasExportCSSView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('account/login/', LoginView.as_view(template_name='account/login.html'), name='account_login'),
    path('account/logout/', require_POST(LogoutView.as_view(next_page='home')), name='account_logout'),
    path("account/profile/<uuid:person_id>/", IntegrantesGetView.as_view(), name='account_user_detail'),
    path('account/profile/edit', edit_profile, name='account_profile_edit'),
    path('account/credentials/edit/', edit_account_info, name='account_login_info_edit'),
    path('account/password_change/', change_password, name='change_password'),
    path('update_role/', UpdateRoleView.as_view(), name='update_role'),
    path('account/signup/', SignUpView.as_view(), name='account_signup'),
    path('account/excluir/', delete_account, name='account_delete'),
    path('account/password_reset/', PassResetView.as_view(), name='account_reset_password'),

    path('account/lista_integrantes', IntegrantesListaView.as_view(), name='admin_integ_list'),

    path('equipes/', EquipesView.as_view(), name='equipes_list'),
    path('equipes/novo/', EquipesCreateView.as_view(), name='equipes_create'),
    path('equipes/leave/', EquipesLeaveView.as_view(), name='equipes_leave'),
    path('equipes/<int:equipe_id>/invite/', equipes_invite, name='equipes_invite'),
    path('equipes/editar/<int:pk>/', EquipesUpdateView.as_view(), name='equipes_edit'),
    path("equipes/<int:equipe_id>", EquipesGetView.as_view(), name='equipes_detail'),
    path('equipes/<int:equipe_id>/projetos/', assign_project, name='equipes_projetos'),
    path('equipes/<int:equipe_id>/remove_projeto/', remove_project, name='remove_projeto'),
    path('equipes/<int:pk>/excluir/', EquipesDeleteView.as_view(), name='equipes_delete'),

    path('projetos/', ProjetosView.as_view() , name='projetos_list'),
    path('projetos/novo/', ProjetosCreateView.as_view(), name='projetos_create'),
    path('projetos/editar/<int:pk>/', ProjetosUpdateView.as_view(), name='projetos_edit'),
    path("projetos/<int:projeto_id>", ProjetosGetView.as_view(), name='projetos_detail'),
    path('projetos/<int:pk>/excluir/', ProjetosDeleteView.as_view(), name='projetos_delete'),
    path('projetos/<int:projeto_id>/export-tasks/', TarefasExportCSSView.as_view(), name='projetos_tarefas_csv'),

    path('tarefas/<int:task_id>/', TarefasAssign.as_view(), name='tarefas_assign'),
    path('projetos/<int:projeto_id>/tarefas/novo/', TarefasCreateView.as_view(),name='tarefas_create'),
    path('tarefas/editar/<int:pk>/', TarefasUpdateView.as_view(), name='tarefas_edit'),
    path('tarefas/excluir/<int:pk>/', TarefasDeleteView.as_view(), name='tarefas_delete'),
    path('tarefas/<int:pk>/', TarefasDetailView.as_view(), name='tarefas_detail'),
    path('tarefas/concluir/<int:task_id>/', TarefasReportView.as_view(), name='tarefas_report'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
