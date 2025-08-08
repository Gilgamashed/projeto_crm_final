from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from projeto_crm_final.models import Integrantes, Equipes

User = get_user_model()


class IntegrantesAccessTest(TestCase):
    def setUp(self):
        self.client= Client()

        #usuario candidato
        self.integrante_user = User.objects.create_user(username='membroTest1', password='senha@123')
        self.integrante = Integrantes.objects.create(
            user=self.integrante_user,
            nome='Teste',
            sobrenome='Testeson jr.',
            email='mtest@email.com',
            role='MEMBER',
            cargo='Crashtest dummy',
            equipe='Alpha',
            telefone='21 123456789',
        )

        #usuario lead
        self.integrante_user = User.objects.create_user(username='leadTest1', password='senha@123')
        self.integrante = Integrantes.objects.create(
            user=self.integrante_user,
            nome='Teste',
            sobrenome='Testeson',
            email='ltest@email.com',
            role='LEAD',
            cargo='Crashtest dummy',
            equipe='Teste duro',
            telefone='21 123456789',
        )

        #usuario admin
        self.integrante_user = User.objects.create_user(username='adminTest1', password='senha@123')
        self.integrante = Integrantes.objects.create(
            user=self.integrante_user,
            nome='Teste',
            sobrenome='Testeson sr.',
            email='atest@email.com',
            role='ADMIN',
            cargo='Crashtest dummy',
            equipe='Alpha',
            telefone='21 123456789',
        )

        # Equipe criada por lead
        self.equipe = Equipes.objects.create(
            name = 'Teste duro',
            descricao = 'Pede pra testar',
        )

        self.url_dashboard= reverse('dashboard', args=[self.integrantes.person_id])

    def teste_integrante_faz_login(self):
        self.client.login(username='membroTest1', password='senha@123')
        response = self.client.get(self.url_dashboard)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Seu painel')