![Coverage](https://img.shields.io/badge/coverage-81%25-brightgreen)

# 👥 Projeto CRM - Gestão de Projetos e Equipes

Sistema web desenvolvido com Django para **gestão de projetos, tarefas e colaboração em equipe**. Conecta líderes de equipe, membros e projetos em uma plataforma centralizada.

---

## 🚀 Funcionalidades Principais

### 👤 Autenticação e Perfis
- Login e logout de usuários
- Dois tipos de perfis:
  - **Membros**: Visualizam tarefas, projetos e enviam relatórios
  - **Líderes de Equipe**: Gerenciam projetos, tarefas e membros

### 📊 Gestão de Projetos
- Criação de projetos com prazos, prioridades e categorias
- Limite de 1 projeto ativo por equipe simultaneamente
- Relatórios de progresso com upload para Cloudinary

### ✅ Gestão de Tarefas
- Sistema Kanban (A Fazer/Fazendo/Concluído)
- Atribuição direta de responsáveis
- Relatórios de conclusão com descrição e arquivos
- Notificações de prazos e atualizações

### 👥 Gestão de Equipes
- Criação de equipes com líderes e membros
- Visão centralizada de projetos por equipe

---

## 🗃️ Modelos Principais

### `Integrantes` (Membros)
| Campo        | Tipo          | Descrição                     |
|--------------|---------------|-------------------------------|
| user         | OneToOne      | Usuário Django associado      |
| nome         | CharField     |                               |
| sobrenome    | CharField     |                               |
| role         | CharField     | Hierarquia (MEMBER/LEADER)    |
| cargo        | CharField     | Cargo na equipe               |
| equipe       | FK → Equipes  | Equipe associada              |

### `Equipes`
| Campo        | Tipo          | Descrição                     |
|--------------|---------------|-------------------------------|
| name         | CharField     | Nome da equipe                |
| leader       | FK → Integrantes | Líder da equipe            |
| membros      | ManyToMany    | Integrantes da equipe         |

### `Projetos`
| Campo        | Tipo          | Descrição                     |
|--------------|---------------|-------------------------------|
| name         | CharField     | Nome único do projeto         |
| equipe       | FK → Equipes  | Equipe responsável            |
| status       | CharField     | (active/paused/completed)     |
| prazofinal   | DateField     | Data limite                   |

### `Tarefas`
| Campo        | Tipo          | Descrição                     |
|--------------|---------------|-------------------------------|
| projetoparent| FK → Projetos | Projeto relacionado           |
| responsavel  | FK → Integrantes | Responsável pela tarefa    |
| status       | CharField     | (todo/doing/done)             |
| prioridade   | CharField     | (high/regular/low)            |

---

## 🔐 Regras de Acesso

- Apenas usuários **autenticados** podem acessar o dashboard
- **Líderes de equipe** podem:
  - Criar/editar projetos e tarefas
  - Gerenciar membros da equipe
- **Membros** podem:
  - Atualizar status de tarefas
  - Enviar relatórios de progresso
- Restrição de 1 projeto ativo por equipe
- Sem restrição de tarefas pro projeto

---

## 🛠️ Tecnologias Usadas

- Django 5.2
- Bootstrap 5 (UI components)
- Supabase PostgreSQL (Banco de dados)
- Cloudinary (Armazenamento de relatórios)
- `widget_tweaks` (Formulários aprimorados)
- UUID (Identificação segura de objetos)
- Render (Host e deploy)

---

## ⚙️ Configuração (.env)

```env
DEBUG=True
SECRET_KEY=sua-chave-secreta
ALLOWED_HOSTS=*.onrender.com,localhost

# Cloudinary
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Banco de dados
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=usuario
DB_PASSWORD=senha
DB_HOST=localhost
DB_PORT=5432
```

---

## ▶️ Como Executar Localmente

1. Clone o repositório:

```bash
git clone https://github.com/Gilgamashed/projeto_crm_final.git
cd projeto-crm
```

2. Configure ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```
3. Instale dependências:
```bash
pip install -r requirements.txt
```

4. Execute migrações:

```bash
python manage.py migrate
```

5. Inicie o servidor:
```bash
python manage.py runserver
```

 6. Acesse: http://localhost:8000

---
## 🎯 Melhorias Futuras
* Sistema de notificações integrado
* Sistema de autenticação por convite usando tokens únicos
* Calendário de prazos e marcos
* Dashboard interativo
* Métricas de produtividade por equipe/membro

## 🧪 Testes e Cobertura
```bash
### Executar testes
pytest
```
### Ver cobertura
```
pytest --cov=. --cov-report=term-missing --cov-report=html
```

### ✅ Cobertura Atual:

* Gestão de projetos (validação de equipes)

* Fluxo de autenticação

* CRUD de tarefas

## 📄 Licença
Projeto educacional desenvolvido para estudos de Django. Distribuído sob licença MIT.

Key features of this README:
1. **Project-Specific Terminology**: Uses your CRM's terminology (Integrantes, Equipes, Tarefas)
2. **Model-Centric Documentation**: Highlights your unique data structure
3. **Workflow Focus**: Emphasizes your Kanban system and team collaboration features
4. **Visual Consistency**: Matches the structure and badges from your example
5. **Deployment Ready**: Includes environment variables for Cloudinary and PostgreSQL
6. **Future Roadmap**: Suggests improvements based on your home page features

The documentation reflects:
- Your custom models (Integrantes, Equipes, Projetos)
- Business rules (1 active project per team)
- Workflow features (Kanban board, reports)
- Security (role-based access control)
- Infrastructure (Cloudinary for reports)