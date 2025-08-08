# populate_equipes.py
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from projeto_crm_final.models import Integrantes, Equipes

TEAM_NAMES = ["Malkuth", "Yesod", "Hod", "Netzach", "Tiphereth", "Gebura", "Chesed", "Binah", "Hokma", "Keter"]

@transaction.atomic
def create_equipes():
    integrantes = list(Integrantes.objects.all())
    if not integrantes:
        raise RuntimeError("No integrantes found — run populate_integrantes first.")

    # Ensure at least len(TEAM_NAMES) leads exist; if not, promote random members
    leads = list(Integrantes.objects.filter(role="LEAD"))
    need = len(TEAM_NAMES) - len(leads)
    if need > 0:
        members = list(Integrantes.objects.filter(role="MEMBER"))
        random.shuffle(members)
        for m in members[:need]:
            m.role = "LEAD"
            m.save()
        leads = list(Integrantes.objects.filter(role="LEAD"))

    random.shuffle(leads)
    created = []
    used_leads = iter(leads)
    for tname in TEAM_NAMES:
        try:
            leader = next(used_leads)
        except StopIteration:
            leader = random.choice(leads)
        equipe = Equipes.objects.create(
            name=tname,
            descricao=f"Equipe {tname} criada pelo script",
            leader=leader
        )
        # choose 3-8 members excluding leader
        pool = [i for i in integrantes if i != leader]
        random.shuffle(pool)
        count = random.randint(3, 8)
        chosen = pool[:count]
        for m in chosen:
            equipe.membros.add(m)
            if not m.equipe:
                m.equipe = equipe
                m.save()
        # ensure leader is also a member
        equipe.membros.add(leader)
        if not leader.equipe:
            leader.equipe = equipe
            leader.save()
        created.append(equipe)
    return created

class Command(BaseCommand):
    help = "Create Equipes and assign members. Depends on Integrantes."

    def handle(self, *args, **options):
        try:
            equipes = create_equipes()
            self.stdout.write(self.style.SUCCESS(f"Created {len(equipes)} equipes."))
        except RuntimeError as e:
            self.stderr.write(str(e))
