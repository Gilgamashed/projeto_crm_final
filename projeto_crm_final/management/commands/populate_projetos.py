# populate_projetos.py
import os
import random
import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction

from projeto_crm_final.models import Projetos, Equipes, Integrantes

BASE_DIR = os.getcwd()

def read_list(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

@transaction.atomic
def create_projetos(n=10):
    equipes = list(Equipes.objects.all())
    equipes_count = len(equipes)
    leaders = list(Integrantes.objects.filter(role="LEAD"))
    all_integrantes = list(Integrantes.objects.all())

    proj_names = read_list(os.path.join(BASE_DIR, "projetosnames.txt")) or [f"Projeto {i}" for i in range(1, 100)]

    # try to read choices from constants if available
    try:
        from projeto_crm_final.constants import PRIORIDADE, CATEGORIA
        PRIORIDADE_VALUES = [c[0] for c in PRIORIDADE]
        CATEGORIA_VALUES = [c[0] for c in CATEGORIA]
    except Exception:
        PRIORIDADE_VALUES = ["baixa", "regular", "alta", "urgente"]
        CATEGORIA_VALUES = ["dev", "marketing", "ops", "research"]

    created = []

    # If there are teams, create one project per team first (up to n)
    teams_shuffled = equipes.copy()
    random.shuffle(teams_shuffled)

    projects_to_create = n

    # First pass: create up to one project per team
    for equipe in teams_shuffled:
        if projects_to_create <= 0:
            break
        # Use team's leader as criador; fallback to any lead or integrante
        criador = equipe.leader if equipe.leader else (random.choice(leaders) if leaders else (random.choice(all_integrantes) if all_integrantes else None))
        if criador is None:
            raise RuntimeError("No Integrantes found to be project creator. Create integrantes first.")

        name = random.choice(proj_names)
        # avoid duplicate names
        suffix = 1
        base_name = name
        while Projetos.objects.filter(name=name).exists():
            name = f"{base_name} #{suffix}"
            suffix += 1

        inicio = timezone.now() - datetime.timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
        prazofinal = (timezone.now().date() + datetime.timedelta(days=random.randint(1, 30)))

        projeto = Projetos.objects.create(
            name=name,
            descricao=f"Projeto {name} criado para equipe {equipe.name}",
            criador=criador,
            equipe=equipe,
            categoria=random.choice(CATEGORIA_VALUES),
            inicio=inicio,
            prioridade=random.choice(PRIORIDADE_VALUES),
            status='active',
            prazofinal=prazofinal
        )
        created.append(projeto)
        projects_to_create -= 1

    # If we still need to create projects (n > number of teams), create the rest with equipe=None
    if projects_to_create > 0:
        # Choose creators for equipo-less projects: prefer leaders, else any integrante
        possible_creators = leaders if leaders else all_integrantes
        if not possible_creators:
            raise RuntimeError("No Integrantes available to set as project creator.")
        for _ in range(projects_to_create):
            criador = random.choice(possible_creators)
            name = random.choice(proj_names)
            suffix = 1
            base_name = name
            while Projetos.objects.filter(name=name).exists():
                name = f"{base_name} #{suffix}"
                suffix += 1

            inicio = timezone.now() - datetime.timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
            prazofinal = (timezone.now().date() + datetime.timedelta(days=random.randint(1, 30)))

            projeto = Projetos.objects.create(
                name=name,
                descricao=f"Projeto {name} (sem equipe) criado pelo script",
                criador=criador,
                equipe=None,
                categoria=random.choice(CATEGORIA_VALUES),
                inicio=inicio,
                prioridade=random.choice(PRIORIDADE_VALUES),
                status='active',
                prazofinal=prazofinal
            )
            created.append(projeto)

    return created

class Command(BaseCommand):
    help = "Create Projetos. One project per team max. If --num > teams, extra projects created with equipe=None."

    def add_arguments(self, parser):
        parser.add_argument('--num', type=int, default=10, help='Number of projects to create (default 10)')

    def handle(self, *args, **options):
        n = options.get('num', 10)
        equipes_count = Equipes.objects.count()
        if equipes_count == 0:
            self.stdout.write(self.style.WARNING("No equipes found — all projects will be created without teams."))
        projetos = create_projetos(n=n)
        self.stdout.write(self.style.SUCCESS(f"Created {len(projetos)} projetos (one per team up to available teams)."))
