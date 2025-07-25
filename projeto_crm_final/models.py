from django.contrib.auth.models import User
from django.db import models

from projeto_crm_final.constants import HIERARCH


class Integrantes(models.Model):
    username = models.OneToOneField(User, unique=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField('email', unique=True, db_index=True)
    role = models.CharField(max_length=20,choices=HIERARCH,default='MEMBER')

    def __str__(self):
        return self.first_name



# Create your models here.
