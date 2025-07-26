import uuid

from django.contrib.auth.models import User
from django.db import models

from projeto_crm_final.constants import HIERARCH


class Integrantes(models.Model):
    person_id = models.UUIDField(primary_key=True, default=uuid.uuid4(),editable=False)
    user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE, max_length=20)
    nome = models.CharField(max_length=25)
    sobrenome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20,choices=HIERARCH,default='MEMBER')

    def save(self, *args, **kwargs):
        self.user.first_name = self.nome
        self.user.last_name = self.sobrenome
        self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.nome



# Create your models here.
