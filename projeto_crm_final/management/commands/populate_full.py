import random
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projeto_crm_final.models import Integrantes, Equipes, Projetos, Tarefas
from django.utils import timezone


class Command(BaseCommand):
    help = "Populate database with sample data"

    def handle(self, *args, **kwargs):
        # Load data from files
        with open("names.txt", encoding="utf-8") as f:
            names = [line.strip().split("|") for line in f if "|" in line]

        with open("cargos.txt", encoding="utf-8") as f:
            cargos = [line.strip() for line in f if line.strip()]
            cargos = [cargo[:20] for cargo in cargos]  # Ensure max length

        with open("projectname.txt", encoding="utf-8") as f:
            project_names = [line.strip() for line in f if line.strip()]

        with open("tarefasnames.txt", encoding="utf-8") as f:
            task_names = [line.strip() for line in f if line.strip()]

        task_descriptions = [
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

        # Create all integrantes
        integrantes = self.create_integrantes(names, cargos)

        # Create teams
        team_names = ["Malkuth", "Yesod", "Hod", "Netzach", "Tiphereth",
                      "Gebura", "Chesed", "Binah", "Hokma", "Keter"]
        teams = self.create_teams(team_names, integrantes)

        # Create projects
        categories = ['Tecnologia da Informação','Marketing','Vendas','Finanças','Recursos Humanos','Serviço ao Cliente',
                      'Operações','Pesquisa & Desenvolvimento','Logística','Jurídico']
        priorities = ['baixa', 'regular', 'alta', 'urgente']
        projects = self.create_projects(project_names, teams, categories, priorities)

        # Create tasks
        self.create_tasks(task_names, task_descriptions, projects, priorities)

        self.stdout.write(self.style.SUCCESS("Database populated successfully!"))

    def create_integrantes(self, names, cargos):
        """Batch-optimized integrante creation"""
        integrantes = []
        user_id_counter = 1
        total_leads_needed = 10
        batch_size = 50  # Process in batches to avoid timeouts

        # Shuffle and process in batches
        random.shuffle(names)

        for i in range(0, len(names), batch_size):
            batch = names[i:i + batch_size]
            user_batch = []
            integrante_batch = []

            for first, last in batch:
                first = first.strip()
                last = last.strip()

                # Generate unique username
                username = f"{first.lower()}{last[0].lower()}{random.randint(10, 99)}"

                # Determine role (first 10 become LEADs)
                role = 'LEAD' if i + batch.index((first, last)) < total_leads_needed else \
                    random.choices(['MEMBER', 'ADMIN'], weights=[0.94, 0.06])[0]

                # Prepare User
                user_batch.append(User(
                    id=user_id_counter,
                    username=username,
                    password="defaultpass",
                    first_name=first,
                    last_name=last,
                    email=f"{username}@email.com"
                ))

                # Prepare Integrante
                phone = f"{'219' if random.random() > 0.5 else '9'}{random.randint(1000000, 9999999)}"
                integrante_batch.append(Integrantes(
                    person_id=uuid.uuid4(),
                    user_id=user_id_counter,  # Reference instead of object
                    nome=first,
                    sobrenome=last,
                    telefone=phone,
                    role=role,
                    cargo=random.choice(cargos)
                ))

                user_id_counter += 1

            # Bulk create users then integrantes
            User.objects.bulk_create(user_batch)
            Integrantes.objects.bulk_create(integrante_batch)

            # Update the integrantes list with actual objects
            batch_integrantes = Integrantes.objects.filter(
                user_id__in=[u.id for u in user_batch]
            )
            integrantes.extend(batch_integrantes)

        return integrantes

    def create_teams(self, team_names, integrantes):
        """Create teams with leaders and members"""
        teams = []
        leads = []

        # First collect all available LEAD and ADMIN users
        potential_leads = [i for i in integrantes if i.role in ['LEAD', 'ADMIN']]

        for name in team_names:
            # Get a leader (ensure each team has a unique leader)
            if potential_leads:
                leader = random.choice(potential_leads)
                potential_leads.remove(leader)
                leads.append(leader)
            else:
                # If no more leads, promote a member to LEAD
                member = random.choice([i for i in integrantes if i.role == 'MEMBER'])
                member.role = 'LEAD'
                member.save()
                leader = member
                leads.append(leader)

            # Create team
            team = Equipes.objects.create(
                name=name,
                descricao=f"Equipe responsável por projetos {name}",
                leader=leader
            )

            # Add members (3-8 per team including the leader)
            num_members = random.randint(3, 8)
            members = random.sample(integrantes, min(num_members, len(integrantes)))

            # Ensure leader is included
            if leader not in members:
                members.append(leader)

            for member in members:
                team.membros.add(member)
                # Set team for member
                member.equipe = team
                member.save()

            teams.append(team)

        return teams

    def create_projects(self, project_names, teams, categories, priorities):
        """Create projects assigned to teams"""
        projects = []
        status_choices = ['active']

        for name in project_names:
            # 80% chance to assign to a team, 20% no team
            team = random.choice(teams) if random.random() < 0.8 else None

            if team:
                # Project creator is the team leader
                creator = team.leader
            else:
                # If no team, pick any integrante
                creator = random.choice(Integrantes.objects.all())

            # Random dates
            start_date = timezone.now() - timedelta(days=random.randint(1, 7))
            end_date = timezone.now() + timedelta(days=random.randint(1, 30))

            project = Projetos.objects.create(
                name=name,
                descricao=f"Descrição do projeto {name}",
                criador=creator,
                equipe=team,
                categoria=random.choice(categories),
                inicio=start_date,
                prioridade=random.choice(priorities),
                status=random.choice(status_choices),
                prazofinal=end_date
            )
            projects.append(project)

        return projects

    def create_tasks(self, task_names, descriptions, projects, priorities):
        """Create tasks assigned to projects"""
        status_choices = ['todo', 'doing', 'done']

        for project in projects:
            if not project.equipe:
                continue  # Skip projects without a team

            # Create 3-10 tasks per project
            num_tasks = random.randint(3, 10)
            for _ in range(num_tasks):
                # Select random team member (20% chance for no responsible)
                team_members = list(project.equipe.membros.all())
                responsible = random.choice(team_members) if random.random() < 0.8 else None

                Tarefas.objects.create(
                    name=random.choice(task_names),
                    descricao=random.choice(descriptions),
                    projetoparent=project,
                    equipe=project.equipe,
                    responsavel=responsible,
                    status=random.choice(status_choices),
                    prazofinal=project.prazofinal,
                    inicio=project.inicio,
                    prioridade=random.choice(priorities)
                )