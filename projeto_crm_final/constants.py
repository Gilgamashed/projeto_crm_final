#importar no models.py e forms.py

STATUS = [
    ('todo','Para fazer'),
    ('doing','Em andamento'),
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
    ('dev', 'dev'),
    ('TI', 'Tecnologia da Informação'),
    ('MK', 'Marketing'),
    ('VD', 'Vendas'),
    ('FN', 'Finanças'),
    ('RH', 'Recursos Humanos'),
    ('CS', 'Serviço ao Cliente'),
    ('OP', 'Operações'),
    ('PD', 'Pesquisa & Desenvolvimento'),
    ('LG', 'Logística'),
    ('JR', 'Jurídico'),
]

STATUSPROJETO = [
    ('active', 'Ativo'),
    ('canceled', 'Cancelado'),
    ('overdue', 'Data vencida'),
    ('done','Concluído')
]

PRIORIDADE = [
    ('baixa','Baixa'),
    ('regular', 'Regular'),
    ('alta', 'Alta'),
    ('urgente', 'Urgente')
]
