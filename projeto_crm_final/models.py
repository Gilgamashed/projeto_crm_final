import uuid

from django.contrib.auth.models import User
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

    def __str__(self):
        return f"{self.nome}"

class Projetos(models.Model):
    name = models.CharField(max_length=200, unique=True)
    descricao = models.TextField(max_length=300, blank=True)
    criador = models.ForeignKey(Integrantes, on_delete=models.CASCADE)
    equipe = models.ForeignKey(Equipes, on_delete=models.SET_NULL, null=True)
    categoria = models.CharField(max_length=100, choices=CATEGORIA, default='null')
    inicio = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUSPROJETO, default='active')
    prazofinal = models.DateField()

    def __str__(self):
        return self.name


class Tarefas(models.Model):
    tarefa = models.CharField(max_length=200)
    descricao = models.TextField()
    projeto = models.ForeignKey(Projetos, on_delete=models.CASCADE)
    equipe = models.ForeignKey(Equipes, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Integrantes, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=15, choices=STATUS, default='parafazer')
    prazofinal = models.DateField()
    inicio = models.DateField(auto_now_add=True)
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE)

    def __str__(self):
        return f"{self.tarefa} - {self.status} - {self.prazofinal}"

class AuditLog(models.Model):
    usuario = models.ForeignKey(Integrantes, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)       #o que ocorreu
    onde = models.CharField(max_length=100)         #aonde ocorreu a mudança
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)



# Create your models here.
