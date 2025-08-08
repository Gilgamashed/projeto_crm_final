from projeto_crm_final.models import Integrantes, Projetos


def navbar_context(request):
    context = {
        'current_user_profile': None,
        'active_projeto': None,
        'active_equipe': None,
        'has_team': False,
    }

    if request.user.is_authenticated:
        try:        #perfil usuario
            profile = Integrantes.objects.get(user=request.user)
            context['current_user_profile'] = profile

            if profile.equipe:      #equipee usuario
                context['active_equipe'] = profile.equipe
                context['has_team'] = True
                                                    #projeto usuario
                context['active_projeto'] = Projetos.objects.filter(
                    equipe=profile.equipe,
                    status='active'
                ).first()

        except Integrantes.DoesNotExist:
            pass

    return context

