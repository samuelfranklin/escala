# Plano de Refatoração - Lógica → Testes → Services → UI

## Estrutura Final
```
helpers/
  __init__.py
  casais.py           # Funções puras de lógica de casais
  disponibilidade.py  # Validação e processamento de disponibilidade
  membros.py          # Validação e processamento de membros
  squads.py           # Validação e processamento de squads
  eventos.py          # Validação e processamento de eventos
  escala_generator.py # Algoritmo de geração de escala
  
services/
  __init__.py
  casais_service.py           # Orquestra helpers + DB
  disponibilidade_service.py  # Orquestra helpers + DB
  membros_service.py          # (já existente, refatora)
  squads_service.py           # Orquestra helpers + DB
  eventos_service.py          # Orquestra helpers + DB
  escala_service.py           # Orquestra helpers + DB
  
tests/
  helpers/
    test_casais.py
    test_disponibilidade.py
    test_membros.py
    test_squads.py
    test_eventos.py
    test_escala_generator.py
  services/
    test_casais_service.py
    test_disponibilidade_service.py
    test_membros_service.py
    test_squads_service.py
    test_eventos_service.py
    test_escala_service.py

gui/
  casais_orm.py           # REFATORADO - só chama service
  disponibilidade_orm.py  # REFATORADO - só chama service
  membros.py              # REFATORADO - só chama service
  squads.py               # REFATORADO - só chama service
  eventos_orm.py          # REFATORADO - só chama service
  gerar_escala.py         # REFATORADO - só chama service
  visualizar.py           # REFATORADO - só chama service
```

## Módulos a Refatorar (ordem)

### 1. CASAIS (Mais Isolado)
**Lógica identificada:**
- Validar que cônjuge 1 ≠ cônjuge 2
- Validar que nenhum dos dois já está em outro casal
- Criar/atualizar/deletar casais

**Files:**
- `helpers/casais.py` - Funções puras
- `tests/helpers/test_casais.py` - Testes TDD
- `services/casais_service.py` - Orquestra DB + helpers
- `gui/casais_orm.py` - Refatorado (chama service)

---

### 2. DISPONIBILIDADE
**Lógica identificada:**
- Validar formato de data (DD/MM/YYYY)
- Validar que data não está no passado
- Processar restrições de disponibilidade
- Verificar se membro está disponível em data/horário

**Files:**
- `helpers/disponibilidade.py` - Funções puras
- `tests/helpers/test_disponibilidade.py` - Testes TDD
- `services/disponibilidade_service.py` - Orquestra DB + helpers
- `gui/disponibilidade_orm.py` - Refatorado (chama service)

---

### 3. MEMBROS
**Lógica identificada:**
- Validar nome (não vazio, única)
- Validar patente (Líder, Treinador, Membro, Recruta)
- Atribuir/remover de squads
- Contar escalas por membro

**Files:**
- `helpers/membros.py` - Funções puras
- `tests/helpers/test_membros.py` - Testes TDD
- `services/membros_service.py` - Refatorar existente
- `gui/membros.py` - Refatorado (chama service)

---

### 4. SQUADS
**Lógica identificada:**
- Validar nome squad (não vazio, único)
- Adicionar/remover membros com patente
- Validar que membro não está 2x no mesmo squad

**Files:**
- `helpers/squads.py` - Funções puras
- `tests/helpers/test_squads.py` - Testes TDD
- `services/squads_service.py` - Orquestra DB + helpers
- `gui/squads.py` - Refatorado (chama service)

---

### 5. EVENTOS
**Lógica identificada:**
- Validar nome evento (não vazio, único)
- Validar tipo (fixo, sazonal)
- Para tipo "fixo": validar dia da semana
- Para tipo "sazonal": validar data
- Validar horário (formato HH:MM)
- Associar squads necessárias + quantidades

**Files:**
- `helpers/eventos.py` - Funções puras
- `tests/helpers/test_eventos.py` - Testes TDD
- `services/eventos_service.py` - Orquestra DB + helpers
- `gui/eventos_orm.py` - Refatorado (chama service)

---

### 6. ESCALA GENERATOR (Mais Complexo)
**Lógica identificada:**
- Coletar eventos do mês/ano
- Para cada evento → buscar squads necessárias
- Para cada squad → buscar membros disponíveis
- Processar casais (escalar juntos se opção ativa)
- Aplicar equilibrio (membros menos escalados primeiro)
- Validar conflitos (faltam membros?)
- Retornar escala alocada

**Files:**
- `helpers/escala_generator.py` - ALGORITMO PURO
- `tests/helpers/test_escala_generator.py` - Testes TDD
- `services/escala_service.py` - Orquestra DB + helpers
- `gui/gerar_escala.py` - Refatorado (chama service)

---

### 7. VISUALIZAR (Menos Lógica)
**Lógica identificada:**
- Filtrar escala por período
- Exportar para CSV
- Validações simples de exibição

**Files:**
- `helpers/visualizar.py` - Funções puras
- `tests/helpers/test_visualizar.py` - Testes TDD
- `services/visualizar_service.py` - Orquestra
- `gui/visualizar.py` - Refatorado (chama service)

---

## Workflow TDD Para Cada Módulo

1. **Escrever testes primeiro** (RED - falham)
2. **Implementar helpers** com funções puras (GREEN)
3. **Implementar services** que usam helpers + DB
4. **Refatorar GUI** para chamar services (remover lógica)

### Exemplo: Casais

#### Passo 1: Escrever testes (tests/helpers/test_casais.py)
```python
def test_validates_different_spouses():
    """Cônjuge 1 ≠ cônjuge 2"""
    assert validate_spouse_ids("alice", "alice") == False
    assert validate_spouse_ids("alice", "bob") == True

def test_prevents_duplicate_couples():
    """Não permite cônjuge em 2 casais"""
    # [fixtures de BD]
    # Criar: Alice + Bob
    # Tentar: Alice + Charlie
    # Deve falhar
```

#### Passo 2: Implementar helpers (helpers/casais.py)
```python
def validate_spouse_ids(spouse1_id: str, spouse2_id: str) -> bool:
    """Cônjuge 1 ≠ cônjuge 2"""
    return spouse1_id != spouse2_id

def validate_couple_unique(spouse1_id: str, spouse2_id: str, session) -> bool:
    """Nenhum dos dois está em outro casal"""
    # Busca na BD...
```

#### Passo 3: Services (services/casais_service.py)
```python
def create_couple(spouse1_id: str, spouse2_id: str) -> FamilyCouple:
    """Orquestra validação + BD"""
    if not helpers.validate_spouse_ids(spouse1_id, spouse2_id):
        raise ValueError("Cônjuges devem ser diferentes")
    
    with session_scope() as session:
        if not helpers.validate_couple_unique(spouse1_id, spouse2_id, session):
            raise ValueError("Pelo menos um já está em outro casal")
        
        couple = FamilyCouple(spouse1_id=spouse1_id, spouse2_id=spouse2_id)
        session.add(couple)
        session.commit()
    
    return couple
```

#### Passo 4: GUI (gui/casais_orm.py)
```python
def cadastrar(self):
    """Chama service, não tem lógica"""
    try:
        spouse1 = self.combo1.get()
        spouse2 = self.combo2.get()
        
        # Só chama service
        casais_service.create_couple(spouse1, spouse2)
        
        messagebox.showinfo("Sucesso", "Casal cadastrado!")
        self._refresh_data()
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
```

---

## Padrões a Seguir

### Helpers (funções puras)
- ✅ Sem acesso a BD (recebem dados via parâmetro)
- ✅ Sem side-effects
- ✅ Fáceis de testar
- ✅ Reutilizáveis em qualquer contexto

### Services (orquestra lógica + BD)
- ✅ Chamam helpers
- ✅ Usam `session_scope()` para BD
- ✅ Tratam exceções
- ✅ Retornam modelos ou raises exceções

### GUI (thin layer)
- ✅ Só chamam services
- ✅ Sem lógica de negócio
- ✅ Formatação visual
- ✅ Tratamento de erros (messagebox)

---

## Métricas de Sucesso

- [ ] 100% coverage em helpers
- [ ] Cada helper testado isoladamente
- [ ] Services testados com mocks de BD
- [ ] GUI sem lógica (só chama service)
- [ ] Nenhuma duplicação de código
- [ ] Módulos completamente isolados

---

## Paralelização

Você pode executar múltiplos agentes em paralelo para:
1. **Casais** + **Disponibilidade** (totalmente independentes)
2. **Membros** (base para Squads)
3. **Squads** (depende de Membros)
4. **Eventos** (independente)
5. **Escala Generator** (último, usa tudo)
6. **Visualizar** (último)

