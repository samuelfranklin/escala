# 🚀 QUICK START - Começar Refatoração GUI (Fase 2)

**Objetivo**: Refatorar frames GUI para usar services ao invés de lógica inline

---

## ⚡ TL;DR (5 minutos)

1. **Escolha um frame** (ex: `gui/casais_orm.py`)
2. **Adicione import**: `from services.casais_service import CasaisService`
3. **No `__init__`**: `self.service = CasaisService()`
4. **Em cada método CRUD**: Substitua lógica por `self.service.operacao()`
5. **Teste**: `python app.py` e teste manualmente

---

## 📋 Template: Antes vs. Depois

### ANTES (com lógica inline)
```python
# gui/casais_orm.py
from infra.database import FamilyCouple, session_scope

def cadastrar(self):
    spouse1 = self.combo1.get()
    spouse2 = self.combo2.get()
    
    if spouse1 == spouse2:
        messagebox.showerror("Erro", "Cônjuges devem ser diferentes")
        return
    
    with session_scope() as session:
        existe = session.query(FamilyCouple).filter(
            (FamilyCouple.member1_id == spouse1) & 
            (FamilyCouple.member2_id == spouse2)
        ).first()
        if existe:
            messagebox.showerror("Erro", "Casal já existe")
            return
        
        novo = FamilyCouple(member1_id=spouse1, member2_id=spouse2)
        session.add(novo)
        session.commit()
    
    messagebox.showinfo("Sucesso", "Casal criado!")
    self._refresh_data()
```

### DEPOIS (thin layer)
```python
# gui/casais_orm.py
from services.casais_service import CasaisService

def __init__(self, parent):
    super().__init__(parent)
    self.service = CasaisService()  # ← NOVO
    # ... resto do init

def cadastrar(self):
    spouse1 = self.combo1.get()
    spouse2 = self.combo2.get()
    
    try:
        self.service.create_couple(spouse1, spouse2)  # ← SIMPLIFICADO
        messagebox.showinfo("Sucesso", "Casal criado!")
        self._refresh_data()
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
```

---

## 🎯 Ordem de Refatoração Recomendada

### Nível 1: Isolados (sem dependências)
- [ ] **`gui/casais_orm.py`** (CasaisService)
- [ ] **`gui/disponibilidade_orm.py`** (DisponibilidadeService)

### Nível 2: Dependem de Nível 1
- [ ] **`gui/membros.py`** (MembrosService)
- [ ] **`gui/squads.py`** (SquadsService)

### Nível 3: Dependem de Nível 2
- [ ] **`gui/eventos_orm.py`** (EventosService)

### Nível 4: Complexo (usa tudo)
- [ ] **`gui/gerar_escala.py`** (EscalaService)

### Nível 5: Visualização
- [ ] **`gui/visualizar.py`** (VisualizarService)

---

## 🔥 Quick Guide: Refatorar um Frame

### Passo 1: Abra o arquivo
```bash
code gui/casais_orm.py
```

### Passo 2: Adicione import (top do arquivo)
```python
from services.casais_service import CasaisService
```

### Passo 3: Modifique `__init__`
```python
def __init__(self, parent):
    super().__init__(parent)
    self.service = CasaisService()  # ← NOVO
    # resto do código
```

### Passo 4: Refatore cada método que toca BD

**Procure por:**
- `with session_scope()`
- `session.query(...)`
- `session.add()`
- `session.delete()`
- `session.commit()`

**Substitua por:**
```python
try:
    result = self.service.operacao(...)  # ← Use service
    messagebox.showinfo("Sucesso", "...")
    self._refresh_data()
except ValueError as e:
    messagebox.showerror("Erro", str(e))
```

### Passo 5: Teste
```bash
python app.py
# Teste CRUD (create, read, update, delete)
```

---

## 📚 Referência Rápida de Services

### CasaisService
```python
service.create_couple(spouse1_id, spouse2_id)        # → FamilyCouple
service.find_couple(spouse1_id, spouse2_id)         # → FamilyCouple | None
service.get_all_couples()                           # → list[FamilyCouple]
service.delete_couple(couple_id)                    # → bool
service.member_has_couple(member_id)                # → bool
```

### MembrosService
```python
service.create(name, rank)                          # → Member
service.get_all()                                   # → list[Member]
service.get_by_id(member_id)                        # → Member | None
service.update(member_id, name, rank)               # → bool
service.delete(member_id)                           # → bool
```

### SquadsService
```python
service.create_squad(name)                          # → Squad
service.get_all_squads()                            # → list[Squad]
service.delete_squad(squad_id)                      # → bool
service.add_member_to_squad(squad_id, member_id, patente)  # → bool
service.remove_member_from_squad(squad_id, member_id)      # → bool
service.get_squad_members(squad_id)                 # → list[Member]
```

### EventosService
```python
service.create_event(name, event_type, time, ...)   # → (bool, str, Event)
service.get_all_events()                            # → list[Event]
service.delete_event(event_id)                      # → (bool, str)
```

### EscalaService
```python
service.generate_schedule(month, year, 
                         respect_couples=True,
                         balance_distribution=True)  # → (list, list[conflicts])
```

### VisualizarService
```python
service.get_schedule_for_period(month, year)        # → list[dict]
service.export_to_csv(schedule, filename)           # → bool
```

---

## ✅ Checklist: Refatoração Completa

Para cada frame:

- [ ] Import do service adicionado
- [ ] Service injetado em `__init__`
- [ ] Todas as linhas `with session_scope()` removidas
- [ ] Todas as linhas `session.query()` removidas
- [ ] Try/except em volta de chamadas de service
- [ ] `_refresh_data()` chamado após operações
- [ ] Testado manualmente (CRUD)
- [ ] Nenhum erro no console
- [ ] `self.db` removido (se houver)
- [ ] Commit e push 🎉

---

## 🧪 Testar Refatoração

### 1. Testar Localmente
```bash
python app.py
```

### 2. Executar Suite Atual
```bash
pytest tests/helpers/ -v
pytest tests/services/ -v
```

### 3. Procurar por Erros
```bash
grep -r "session_scope" gui/  # Não deve achar aqui após refatoração
grep -r "session.query" gui/  # Idem
```

---

## 🆘 Problemas Comuns

### Erro: "DetachedInstanceError"
```
sqlalchemy.orm.exc.DetachedInstanceError: 
Instance <Member at 0x...> is not bound to a Session
```

**Solução**: Não acesse atributos lazy após fechar session
```python
# ERRADO
membro = self.service.get_by_id(123)
print(membro.squads)  # ← Lazy load fail

# CERTO
membros = self.service.get_all()  # Já carregados
```

### Erro: "Treeview Vazio Após Refatoração"
```python
# ERRADO - Não atualiza UI
self.service.create(name)

# CERTO
self.service.create(name)
self._refresh_data()  # ← Sempre chamar!
```

### Erro: "Método XXX não existe no service"
```python
# Verificar o service existe em /services/
# Verificar assinatura do método
# Consultar docstring: help(service.metodo)
```

---

## 💡 Pro Tips

1. **Refatore um método por vez**: Faça refatoração → teste → commit
2. **Use o IDE**: Busca/replace para `session_scope` → `self.service`
3. **Teste cada CRUD**: Create, Read, Update, Delete
4. **Mantenha git limpo**: Commits atômicos por frame
5. **Documente erros**: Se encontrar issue, documente para depois

---

## 📞 Documentos de Referência

| Documento | Propósito |
|-----------|----------|
| `/GUI_REFACTORING_GUIDE.md` | Guia detalhado (exemplo completo de Membros) |
| `/REFACTOR_PLAN.md` | Arquitetura geral |
| `/PHASE1_COMPLETION_REPORT.md` | Status e métricas |
| `/AGENTS.md` | Padrões de código |

---

## 🎯 Próximo?

Após refatorar todos os frames:

1. Rodar testes `pytest tests/`
2. Validar cobertura `pytest --cov`
3. Fazer merge para main
4. Deploy em produção 🚀

---

**Pronto? Escolha um frame e comece! 💪**

*Comece com `gui/casais_orm.py` - é o mais simples.*
