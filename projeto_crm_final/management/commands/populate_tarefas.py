# populate_tarefas.py
import os
import random
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from projeto_crm_final.models import Projetos, Tarefas, Equipes

BASE_DIR = os.getcwd()


def read_list(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

@transaction.atomic
def create_tarefas(avg_per_project=3):
    projetos = list(Projetos.objects.all())
    equipes = list(Equipes.objects.all())
    if not projetos:
        raise RuntimeError("No projetos found — run populate_projetos first.")

    tarefa_names = read_list(os.path.join(BASE_DIR, "tarefasnames.txt")) or [
        "Investigate the issue", "The world needs you!", "It's dangerous to go alone!"
    ]
    descriptions = [
            "O mundo precisa de você!",
            "É perigoso ir sozinho!",
            "A força está com você",
            "Que a sorte esteja ao seu favor",
            "A aventura começa agora",
            "Grandes poderes trazem grandes responsabilidades",
            "A esperança é a última que morre",
            "Unidos venceremos",
            "A vitória está próxima",
            "O destino nos espera"
        ]

    created = 0

    try:
        from projeto_crm_final.constants import PRIORIDADE, STATUS
        PRIORIDADE_VALUES = [c[0] for c in PRIORIDADE]
        STATUS_VALUES = [c[0] for c in STATUS]
    except Exception:
        PRIORIDADE_VALUES = ["baixa", "regular", "alta", "urgente"]
        STATUS_VALUES = ["todo", "doing", "done"]

    for projeto in projetos:
        n = max(1, int(random.gauss(avg_per_project, 1)))
        for _ in range(n):
            name = random.choice(tarefa_names)
            descricao = random.choice(descriptions)
            equipe = projeto.equipe or random.choice(equipes) if equipes else None
            membros = list(equipe.membros.all()) if equipe else []
            responsavel = random.choice(membros) if membros and random.random() < 0.8 else None
            status = random.choice(STATUS_VALUES)
            prioridade = random.choice(PRIORIDADE_VALUES)
            tarefa = Tarefas.objects.create(
                name=name,
                descricao=descricao,
                projetoparent=projeto,
                equipe=equipe if equipe else equipes[0] if equipes else None,
                responsavel=responsavel,
                status=status,
                prazofinal=projeto.prazofinal,
                inicio=projeto.inicio,
                prioridade=prioridade
            )
            created += 1
    return created

class Command(BaseCommand):
    help = "Create Tarefas for each Projeto. Depends on Projetos."

    def add_arguments(self, parser):
        parser.add_argument('--avg', type=int, default=3)

    def handle(self, *args, **options):
        try:
            total = create_tarefas(avg_per_project=options['avg'])
            self.stdout.write(self.style.SUCCESS(f"Created {total} tarefas."))
        except RuntimeError as e:
            self.stderr.write(str(e))
