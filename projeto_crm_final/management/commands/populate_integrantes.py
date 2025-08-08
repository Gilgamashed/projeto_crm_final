# populate_integrantes.py
import os
import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from projeto_crm_final.models import Integrantes

BASE_DIR = os.getcwd()

def parse_names_file(path):
    pairs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                left, right = line.split("|", 1)
                pairs.append((left.strip(), right.strip()))
            elif "," in line:
                left, right = line.split(",", 1)
                pairs.append((left.strip(), right.strip()))
            else:
                parts = line.split()
                if len(parts) >= 2:
                    pairs.append((parts[0].strip(), " ".join(parts[1:]).strip()))
                else:
                    pairs.append((parts[0].strip(), ""))
    return pairs

def read_cargos(path, max_len=20):
    res = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if len(s) > max_len:
                s = s[:max_len-1] + "…"
            res.append(s)
    return res

def ensure_min_user_id(min_id):
    # Create dummy users to advance the PK sequence if necessary
    try:
        current_max = User.objects.all().order_by('-id').first().id or 0
    except Exception:
        current_max = 0
    created = 0
    while current_max < (min_id - 1):
        current_max += 1
        uname = f"_dummy_{current_max}"
        if not User.objects.filter(username=uname).exists():
            User.objects.create_user(username=uname, password=uuid.uuid4().hex[:8])
            created += 1
    return created

@transaction.atomic
def create_integrantes(names_path, cargos_path, min_user_id=22):
    names = parse_names_file(names_path)
    cargos = read_cargos(cargos_path) if os.path.exists(cargos_path) else ["Funcionário"]
    ensure_min_user_id(min_user_id)

    created = []
    used_usernames = set(User.objects.values_list('username', flat=True))
    for first, last in names:
        first = first[:25]
        last = last[:100]
        base = (first + (last[0] if last else "")).lower().replace(" ", "")
        # make unique username
        attempts = 0
        while True:
            suffix = random.randint(10, 99)
            username = f"{base}{suffix}"
            if username not in used_usernames and not User.objects.filter(username=username).exists():
                used_usernames.add(username)
                break
            attempts += 1
            if attempts > 50:
                username = f"{base}{uuid.uuid4().hex[:6]}"
                break

        email = f"{username}@email.com"
        user = User.objects.create_user(username=username, password="senha@123", email=email,
                                        first_name=first, last_name=last)
        telefone = f"21{random.choice(['98','99'])}{random.randint(10**6, 10**7-1)}" if random.random() < 0.6 else f"9{random.randint(10**6,10**7-1)}"
        cargo = random.choice(cargos)
        integrante = Integrantes.objects.create(
            person_id=uuid.uuid4(),
            user=user,
            nome=first,
            sobrenome=last,
            telefone=telefone,
            role="MEMBER",
            cargo=cargo
        )
        created.append(integrante)
    return created

class Command(BaseCommand):
    help = "Create Integrantes from names.txt and cargos.txt"

    def add_arguments(self, parser):
        parser.add_argument('--min-user-id', type=int, default=22)

    def handle(self, *args, **options):
        names_file = os.path.join(BASE_DIR, "names.txt")
        cargos_file = os.path.join(BASE_DIR, "cargos.txt")
        if not os.path.exists(names_file):
            self.stderr.write("names.txt not found in project root.")
            return
        created = create_integrantes(names_file, cargos_file, min_user_id=options['min_user_id'])
        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} integrantes."))
