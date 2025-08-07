import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from .constants import HIERARCH, STATUS, PRIORIDADE, CATEGORIA, STATUSPROJETO


class Integrantes(models.Model):
    person_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE, max_length=20)
    nome = models.CharField(max_length=25)
    sobrenome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20,choices=HIERARCH,default='MEMBER',null=False,blank=False)
    cargo = models.CharField(max_length=20, default='Desligado')
    equipe = models.ForeignKey('Equipes', on_delete=models.SET_NULL, null=True, blank=True, max_length=20)

    @property
    def email(self):
        return self.user.email

    def save(self, *args, **kwargs):
        self.user.first_name = self.nome
        self.user.last_name = self.sobrenome
        self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"


class Equipes(models.Model):
    name = models.CharField(max_length=100)
    descricao = models.TextField()
    leader = models.ForeignKey(Integrantes, on_delete=models.CASCADE, related_name="team_boss")
    membros = models.ManyToManyField(Integrantes)

    def add_member(self, integrante):
        """metodo para adicionar membros a equipe - testar"""
        self.membros.add(integrante)
        if not integrante.equipe:
            integrante.equipe = self
            integrante.save()

    def remove_member(self, integrante):
        """Remove um membro da equipe"""
        if integrante in self.membros.all():
            self.membros.remove(integrante)
            if integrante.equipe == self:
                integrante.equipe = None
                integrante.save()
        return True

    def __str__(self):
        return f"{self.name}"

class Projetos(models.Model):
    name = models.CharField(max_length=200, unique=True)
    descricao = models.TextField(max_length=300, blank=True)
    criador = models.ForeignKey(Integrantes, on_delete=models.CASCADE)
    equipe = models.ForeignKey(Equipes, on_delete=models.SET_NULL, null=True)
    categoria = models.CharField(max_length=100, choices=CATEGORIA, default='dev')
    inicio = models.DateTimeField(auto_now_add=True)
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE, default='regular')
    status = models.CharField(max_length=20, choices=STATUSPROJETO, default='active')
    prazofinal = models.DateField()

    def __str__(self):
        return self.name

    def clean(self):
        # Checagem pra ver se o projeto está ativo e relacionado à uma equipe
        if self.status == 'active' and self.equipe:
            existing_active = Projetos.objects.filter(
                equipe=self.equipe,
                status='active'
            ).exclude(pk=self.pk).first()

            if existing_active:
                raise ValidationError(
                    f"A equipe {self.equipe.name} já tem um projeto ativo: "
                    f"{existing_active.name}. Remova-o antes de adicionar um novo."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class RelatorioProjeto(models.Model):
    projeto = models.ForeignKey(Projetos, on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to='relatorios/')
    enviado_por = models.ForeignKey(Integrantes, on_delete=models.CASCADE)
    enviado_em = models.DateTimeField(auto_now_add=True)
    cloudinary_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Relatório para {self.projeto.name}"


class Tarefas(models.Model):
    name = models.CharField(max_length=200)
    descricao = models.TextField()
    projetoparent = models.ForeignKey(Projetos, on_delete=models.CASCADE, related_name="tarefas_do_projeto")
    equipe = models.ForeignKey(Equipes, on_delete=models.CASCADE, verbose_name="Equipe Responsável")
    responsavel = models.ForeignKey(Integrantes, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Responsável Direto")
    status = models.CharField(max_length=15, choices=STATUS, default='todo')
    prazofinal = models.DateField()
    inicio = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE, default='regular')

    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ['prazofinal']


    def save(self, *args, **kwargs):
        if not self.equipe_id and self.projetoparent_id:
            self.equipe = self.projetoparent.equipe
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} | {self.get_status_display()}"


class AuditLog(models.Model):
    usuario = models.ForeignKey(Integrantes, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)       #o que ocorreu
    onde = models.CharField(max_length=100)         #aonde ocorreu a mudança
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)



# Create your models here.
