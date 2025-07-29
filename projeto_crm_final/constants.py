#importar no models.py e forms.py

STATUS = [
    ('todo','Para fazer'),
    ('analise','Em analise'),
    ('debater','A debater'),
    ('emandamento','Em andamento'),
    ('done','Feito'),
    ('late','Atrasada'),
    ('canceled','Cancelada')
]

HIERARCH = [
    ('ADMIN', 'Gerencia'),
    ('LEAD', 'Lider de Equipe'),
    ('MEMBER', 'Membro'),
    ('GUEST', 'Acesso Limitado')
]

CATEGORIA = [
    ('null', 'Não específico'),
    ('dev', 'dev'),
]

STATUSPROJETO = [
    ('active', 'Ativo'),
    ('canceled', 'Cancelado'),
    ('expired', 'Data vencida'),
    ('done','Concluído')
]

PRIORIDADE = [
    ('baixa','Baixa'),
    ('regular', 'Regular'),
    ('alta', 'Alta'),
    ('urgente', 'Urgente')
]
