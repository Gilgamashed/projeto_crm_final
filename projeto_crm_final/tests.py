from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from projeto_crm_final.models import Integrantes, Equipes


class IntegrantesAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

        # usuario candidato (member)
        self.member_user = User.objects.create_user(
            username='membroTest1', password='senha@123'
        )
        self.member_integrante = Integrantes.objects.create(
            user=self.member_user,
            nome='Teste',
            sobrenome='Testeson jr.',
            role='MEMBER',
            cargo='Crashtest dummy',
            telefone='21 123456789',
        )

        # usuario lead
        self.lead_user = User.objects.create_user(
            username='leadTest1', password='senha@123'
        )
        self.lead_integrante = Integrantes.objects.create(
            user=self.lead_user,
            nome='Teste',
            sobrenome='Testeson',
            role='LEAD',
            cargo='Crashtest dummy',
            telefone='21 123456789',
        )

        # usuario admin
        self.admin_user = User.objects.create_user(
            username='adminTest1', password='senha@123'
        )
        self.admin_integrante = Integrantes.objects.create(
            user=self.admin_user,
            nome='Teste',
            sobrenome='Testeson sr.',
            role='ADMIN',
            cargo='Crashtest dummy',
            telefone='21 123456789',
        )

        # Equipe criada por lead
        self.equipe = Equipes.objects.create(
            name='Teste duro',
            descricao='Pede pra testar',
            leader=self.lead_integrante
        )

        # Pgaina do usuario URL
        self.url_dashboard = reverse(
            'account_user_detail', args=[self.member_integrante.person_id]
        )

    def test_member_can_login_and_access_userpage(self):
        login_ok = self.client.login(
            username='membroTest1', password='senha@123'
        )
        self.assertTrue(login_ok, "Login should succeed for member user")

        response = self.client.get(self.url_dashboard)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perfil de')

class AuthBaseTest(TestCase):
    def create_user_and_integrante(self, username, password, email, nome, sobrenome, role='MEMBER'):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        integrante = Integrantes.objects.create(
            user=user,
            nome=nome,
            sobrenome=sobrenome,
            telefone='21 999999999',
            role=role,
            cargo='Tester',
        )
        return user, integrante

class AuthenticationFlowTest(AuthBaseTest):
    def setUp(self):
        self.password = 'senha@123'
        self.user, self.integrante = self.create_user_and_integrante(
            username='membroTest1',
            password=self.password,
            email='mtest@email.com',
            nome='Teste',
            sobrenome='Testeson Jr.'
        )

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse('account_login'),
            {'username': self.user.username, 'password': self.password}
        )
        self.assertEqual(response.status_code, 302)  # redireciona
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            reverse('account_login'),
            {'username': self.user.username, 'password': 'wrongpass'}
        )
        self.assertEqual(response.status_code, 200)  # fica na pagina de login
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_requires_post(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(reverse('account_logout'))
        self.assertEqual(response.status_code, 302)  # redirect pra home
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_logout_with_get_is_not_allowed(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse('account_logout'))
        self.assertEqual(response.status_code, 405)  # metodo nao permitido


class ProfileTest(AuthBaseTest):
    def setUp(self):
        self.password = 'senha@123'
        self.user, self.integrante = self.create_user_and_integrante(
            username='membroTest1',
            password=self.password,
            email='mtest@email.com',
            nome='Teste',
            sobrenome='Testeson Jr.'
        )

    def test_view_own_profile(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse('account_user_detail', args=[self.integrante.person_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.integrante.nome)

    def test_edit_profile(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse('account_profile_edit')
        response = self.client.post(url, {
            'nome': 'NovoNome',
            'sobrenome': 'NovoSobrenome',
            'telefone': '21 988888888',
            'cargo': 'QA Tester',
        })
        self.assertEqual(response.status_code, 302)  # ???
        self.integrante.refresh_from_db()
        self.assertEqual(self.integrante.nome, 'NovoNome')

class AccountManagementTest(AuthBaseTest):
    def setUp(self):
        self.password = 'senha@123'
        self.user, self.integrante = self.create_user_and_integrante(
            username='membroTest1',
            password=self.password,
            email='mtest@email.com',
            nome='Teste',
            sobrenome='Testeson Jr.'
        )

    def test_change_password(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse('change_password')
        response = self.client.post(url, {
            'old_password': self.password,
            'new_password1': 'novaSenha@123',
            'new_password2': 'novaSenha@123',
        })
        self.assertEqual(response.status_code, 302)
        # old password should no longer work
        self.client.logout()
        login_old = self.client.login(username=self.user.username, password=self.password)
        self.assertFalse(login_old)
        # new password works
        login_new = self.client.login(username=self.user.username, password='novaSenha@123')
        self.assertTrue(login_new)

    def test_edit_login_info(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse('account_login_info_edit')
        response = self.client.post(url, {
            'username': 'novoUsername',
            'email': 'novo@email.com'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'novoUsername')

    def test_delete_account(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse('account_delete')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=self.user.pk)

class TeamCRUDTest(TestCase):
    def setUp(self):
        # Create leader
        self.leader_user = User.objects.create_user(
            username='lead', password='senha@123', email='lead@email.com'
        )
        self.leader_integrante = Integrantes.objects.create(
            user=self.leader_user,
            nome='Lead',
            sobrenome='One',
            telefone='21 999999999',
            role='LEAD',
            cargo='Leader',
        )

        # Create member
        self.member_user = User.objects.create_user(
            username='member', password='senha@123', email='member@email.com'
        )
        self.member_integrante = Integrantes.objects.create(
            user=self.member_user,
            nome='Member',
            sobrenome='One',
            telefone='21 999999999',
            role='MEMBER',
            cargo='Member',
        )

        # Create existing team
        self.team = Equipes.objects.create(
            name='Team Alpha',
            descricao='Test team',
            leader=self.leader_integrante
        )

#Crud de equipes

    def test_leader_can_create_team(self):
        self.client.login(username='lead', password='senha@123')
        response = self.client.post(reverse('equipes_create'), {
            'name': 'Team Beta',
            'descricao': 'Another team',
            'leader': self.leader_integrante.pk
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Equipes.objects.filter(name='Team Beta').exists())

    def test_any_logged_in_user_can_view_team_detail(self):
        self.client.login(username='member', password='senha@123')
        response = self.client.get(reverse('equipes_detail', args=[self.team.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Alpha')

    def test_leader_can_update_team(self):
        self.client.login(username='lead', password='senha@123')
        response = self.client.post(reverse('equipes_edit', args=[self.team.pk]), {
            'name': 'Team Alpha Updated',
            'descricao': 'Updated description',
            'leader': self.leader_integrante.pk
        })
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'Team Alpha Updated')

    def test_non_leader_cannot_update_team(self):
        self.client.login(username='member', password='senha@123')
        response = self.client.post(reverse('equipes_edit', args=[self.team.pk]), {
            'name': 'Evil Edit',
            'descricao': 'Hacked',
            'leader': self.member_integrante.pk
        })
        self.assertNotEqual(response.status_code, 403)
        self.team.refresh_from_db()
        self.assertNotEqual(self.team.name, 'Evil Edit')

    def test_leader_can_delete_team(self):
        self.client.login(username='lead', password='senha@123')
        response = self.client.post(reverse('equipes_delete', args=[self.team.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Equipes.objects.filter(pk=self.team.pk).exists())

    def test_non_leader_cannot_delete_team(self):
        self.client.login(username='member', password='senha@123')
        response = self.client.post(reverse('equipes_delete', args=[self.team.pk]))
        self.assertNotEqual(response.status_code, 403)      #O Django redireciona entao ...?
        self.assertTrue(Equipes.objects.filter(pk=self.team.pk).exists())
