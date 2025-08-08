import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projeto_crm_final.models import Integrantes

class Command(BaseCommand):
    help = "Populate Integrantes table with random data"

    def handle(self, *args, **kwargs):
        # Load data from files
        with open("names.txt", encoding="utf-8") as f:
            names = [line.strip().split("|") for line in f if "|" in line]

        with open("cargos.txt", encoding="utf-8") as f:
            cargos = [line.strip()[:19] for line in f if line.strip()]

        roles = ["MEMBER", "LEAD", "ADMIN"]

        start_user_id = 2
        num_records = 20  # adjust how many to create

        for i in range(num_records):
            first, last = [n.strip() for n in random.choice(names)]
            username = f"{first.lower()}{last[0].lower()}{random.randint(10,99)}"

            # Create Django User first
            user = User.objects.create_user(
                username=username,
                password="123456",  # default pass, change later
                first_name=first,
                last_name=last,
                email=f"{username}@example.com"
            )

            integrante = Integrantes.objects.create(
                person_id=uuid.uuid4(),
                user=user,
                nome=first,
                sobrenome=last,
                telefone=f"21{random.choice(['98','99'])}{random.randint(1000000,9999999)}",
                role=random.choice(roles),
                cargo=random.choice(cargos)
            )

            self.stdout.write(self.style.SUCCESS(f"Created integrante: {integrante}"))

        self.stdout.write(self.style.SUCCESS("Done populating integrantes!"))