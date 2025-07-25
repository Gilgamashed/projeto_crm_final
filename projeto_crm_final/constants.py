#importar no models.py e forms.py

STATUS = [
    ('parafazer','Para fazer'),
    ('emanalise','Em analise'),
    ('debater','A debater'),
    ('emandamento','Em andamento'),
    ('feito','Feito'),
    ('atrasada','Atrasada'),
    ('Cancelada','Cancelada')
]

HIERARCH = [
    ('ADMIN', 'Gerencia'),
    ('LEAD', 'Lider de Equipe'),
    ('MEMBER', 'Membro'),
    ('GUEST', 'Acesso Limitado')
]

CATEGORIA = [
    ('dev', 'dev'),
]
PRIORIDADE = [
    ('baixa','Baixa'),
    ('regular', 'Regular'),
    ('alta', 'Alta'),
    ('urgente', 'Urgente')
]
