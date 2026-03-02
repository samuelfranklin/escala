# 📖 GUIA: Refatoração de GUI para Chamar Services

**Escopo**: Como transformar frames GUI para usar services (ao invés de lógica inline)

---

## 🎯 Padrão a Seguir

### Antes (GUI com Lógica Inline)
```python
# gui/membros.py - ANTES
import tkinter as tk
from infra.database import Member, session_scope

class MembrosFrame(ttk.Frame):
    def cadastrar(self):
        nome = self.entry_nome.get()
        patente = self.combo_patente.get()
        
        # ❌ LÓGICA INLINE (validação, BD, tudo misturado)
        if not nome or not nome.strip():
            messagebox.showerror("Erro", "Nome obrigatório")
            return
        
        if patente not in ["Líder", "Treinador", "Membro", "Recruta"]:
            messagebox.showerror("Erro", "Patente inválida")
            return
        
        with session_scope() as session:
            existe = session.query(Member).filter(Member.name == nome).first()
            if existe:
                messagebox.showerror("Erro", "Membro já existe")
                return
            
            novo = Member(name=nome, rank=patente, ...)
            session.add(novo)
            session.commit()
        
        messagebox.showinfo("Sucesso", "Membro criado!")
        self._refresh_data()
```

### Depois (GUI Thin - Chama Service)
```python
# gui/membros.py - DEPOIS
import tkinter as tk
from services.membros_service import MembrosService

class MembrosFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.service = MembrosService()  # ← Injetar service
        # ... UI setup
    
    def cadastrar(self):
        # ✅ APENAS UI LOGIC (get input, call service, show resposta)
        nome = self.entry_nome.get()
        patente = self.combo_patente.get()
        
        try:
            self.service.create(nome, patente)  # ← Service cuida de tudo
            messagebox.showinfo("Sucesso", "Membro criado!")
            self._refresh_data()
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
    
    def _refresh_data(self):
        # ✅ APENAS UI (carregar dados, atualizar tree)
        try:
            membros = self.service.get_all()
            self._update_treeview(membros)
        except Exception as e:
            messagebox.showerror("Erro ao carregar", str(e))
```

---

## 📋 Checklist por Frame

### ✅ Template de Refatoração

Para cada frame (`casais_orm.py`, `membros.py`, etc):

1. **Identifique o service correspondente** (ex: `MembrosService`)
2. **No `__init__`, injete o service**:
   ```python
   def __init__(self, parent):
       super().__init__(parent)
       self.service = MembrosService()  # ← AQUI
   ```

3. **Em cada método que toca BD**:
   - ❌ Remova `with session_scope() as session:`
   - ❌ Remova queries diretas (`session.query(...)`)
   - ✅ Substitua por `self.service.operacao(...)`

4. **Em métodos auxiliares** (`_refresh_data`, etc):
   - Chame `self.service.get_all()` ou similar
   - Apenas manipule UI após receber dados

5. **Logo após refatorar**:
   - Rodar app manualmente
   - Testar CRUD: criar, ler, atualizar, deletar
   - Verificar mensagens de erro

---

## 🔄 Exemplo Completo: Refatorar `MembrosFrame`

### Arquivo Original
- `/home/samuel/projects/escala/gui/membros.py` (586 linhas)

### Passo 1: Adicione Import
```python
from services.membros_service import MembrosService
```

### Passo 2: Injetar Service no `__init__`
```python
def __init__(self, parent, db=None):
    super().__init__(parent)
    self.service = MembrosService()  # ← SEU CÓDIGO
    self.db = db  # ← REMOVA DEPOIS
    # ... resto do código
```

### Passo 3: Refatore Método `_adicionar_membro`
**ANTES:**
```python
def _adicionar_membro(self):
    novo_nome = self.entry_novo_membro.get().strip()
    if not novo_nome:
        messagebox.showerror("Erro", "Nome obrigatório")
        return
    
    patente = self.combo_patente.get()
    if patente not in self.patentes:
        messagebox.showerror("Erro", "Patente inválida")
        return
    
    try:
        with session_scope() as session:
            existe = session.query(Member).filter(Member.name == novo_nome).first()
            if existe:
                messagebox.showerror("Erro", "Já existe")
                return
            
            novo = Member(name=novo_nome, rank=patente, ...)
            session.add(novo)
            session.commit()
        
        messagebox.showinfo("Sucesso", "Adicionado!")
        self._atualizar_lista()
    except Exception as e:
        messagebox.showerror("Erro BD", str(e))
```

**DEPOIS:**
```python
def _adicionar_membro(self):
    novo_nome = self.entry_novo_membro.get().strip()
    patente = self.combo_patente.get()
    
    try:
        # Service cuida de validação + BD
        self.service.create(novo_nome, patente)
        messagebox.showinfo("Sucesso", "Membro adicionado!")
        self._atualizar_lista()
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
```

### Passo 4: Refatore `_atualizar_lista`
**ANTES:**
```python
def _atualizar_lista(self):
    self.tree.delete(*self.tree.get_children())
    
    with session_scope() as session:
        membros = session.query(Member).order_by(Member.name).all()
        
        for membro in membros:
            self.tree.insert("", "end", 
                           iid=membro.id,
                           values=(membro.name, membro.rank))
```

**DEPOIS:**
```python
def _atualizar_lista(self):
    self.tree.delete(*self.tree.get_children())
    
    try:
        membros = self.service.get_all()  # ← Service retorna list[Member]
        
        for membro in membros:
            self.tree.insert("", "end",
                           iid=membro.id,
                           values=(membro.name, membro.rank))
    except Exception as e:
        messagebox.showerror("Erro ao carregar", str(e))
```

### Passo 5: Refatore `_remover_membro`
**ANTES:**
```python
def _remover_membro(self):
    selecionado = self.tree.selection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um membro")
        return
    
    membro_id = selecionado[0]
    
    if messagebox.askyesno("Confirmar", "Deletar este membro?"):
        with session_scope() as session:
            session.query(Member).filter(Member.id == membro_id).delete()
            session.commit()
        
        messagebox.showinfo("Sucesso", "Membro removido!")
        self._atualizar_lista()
```

**DEPOIS:**
```python
def _remover_membro(self):
    selecionado = self.tree.selection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um membro")
        return
    
    membro_id = selecionado[0]
    
    if messagebox.askyesno("Confirmar", "Deletar este membro?"):
        try:
            self.service.delete(membro_id)  # ← Service faz tudo
            messagebox.showinfo("Sucesso", "Membro removido!")
            self._atualizar_lista()
        except Exception as e:
            messagebox.showerror("Erro", str(e))
```

---

## 🎯 Services Disponíveis

Você pode usar estes services:

### `MembrosService`
```python
from services.membros_service import MembrosService

service = MembrosService()
service.create(nome, patente) → bool
service.get_all() → list[Member]
service.get_by_id(member_id) → Member | None
service.update(member_id, nome, patente) → bool
service.delete(member_id) → bool
service.assign_to_squad(member_id, squad_id, patente) → bool
service.remove_from_squad(member_id, squad_id) → bool
service.count_member_schedules(member_id) → int
```

### `SquadsService`
```python
from services.squads_service import SquadsService

service = SquadsService()
service.create_squad(name) → Squad
service.update_squad_name(squad_id, new_name) → bool
service.delete_squad(squad_id) → bool
service.add_member_to_squad(squad_id, member_id, patente) → bool
service.remove_member_from_squad(squad_id, member_id) → bool
service.get_all_squads() → list[Squad]
service.get_squad_members(squad_id) → list[Member]
```

### `EventosService`
```python
from services.eventos_service import EventosService

service = EventosService()
service.create_event(...) → tuple[bool, str, Event]
service.update_event(...) → tuple[bool, str]
service.delete_event(event_id) → tuple[bool, str]
service.get_all_events() → list[Event]
service.get_event_by_id(event_id) → Event | None
service.add_squad_to_event(event_id, squad_id, quantity) → bool
```

### `CasaisService`
```python
from services.casais_service import CasaisService

service = CasaisService()
service.create_couple(spouse1_id, spouse2_id) → FamilyCouple
service.find_couple(spouse1_id, spouse2_id) → FamilyCouple | None
service.delete_couple(couple_id) → bool
service.get_all_couples() → list[FamilyCouple]
service.member_has_couple(member_id) → bool
```

### `DisponibilidadeService`
```python
from services.disponibilidade_service import DisponibilidadeService

service = DisponibilidadeService()
service.create_restriction(member_id, date_str, description) → dict
service.remove_restriction(member_id, date_str) → dict
service.get_restrictions_by_member(member_id) → list[dict]
service.is_member_available_on_date(member_id, date_str) → bool
```

### `EscalaService`
```python
from services.escala_service import EscalaService

service = EscalaService()
schedule, conflicts = service.generate_schedule(
    month, year,
    respect_couples=True,
    balance_distribution=True
) → list[dict], list[str]
```

### `VisualizarService`
```python
from services.visualizar_service import VisualizarService

service = VisualizarService()
service.get_schedule_for_period(month, year) → list[dict]
service.get_squad_allocations(squad_id) → list[dict]
service.export_to_csv(schedule, filename) → bool
```

---

## 🚨 Armadilhas Comuns

### ❌ Erro 1: Esquecer de Try/Except
```python
# ERRADO
def cadastrar(self):
    nome = self.entry.get()
    self.service.create(nome)  # ← Pode lançar ValueError!
    self._refresh()
```

**CORRETO:**
```python
# CERTO
def cadastrar(self):
    nome = self.entry.get()
    try:
        self.service.create(nome)
        messagebox.showinfo("Sucesso", "Criado!")
        self._refresh()
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
```

### ❌ Erro 2: Acessar atributos após session close
```python
# ERRADO
membro = self.service.get_by_id(123)
print(membro.squads)  # ← Lazy loading fail!
```

**CORRETO:**
```python
# CERTO (dentro de service, com session ativa)
# ou buscar joinedload
membro = self.service.get_by_id(123)
# Acessar atributos que foram carregados durante get_by_id
```

### ❌ Erro 3: Não atualizar UI após operação
```python
# ERRADO
def cadastrar(self):
    self.service.create(nome, patente)
    # Treeview NÃO é atualizada!
```

**CORRETO:**
```python
# CERTO
def cadastrar(self):
    self.service.create(nome, patente)
    self._refresh_data()  # ← Sempre atualizar UI
```

---

## ✅ Checklist de Refatoração

Para cada frame, certifique-se de:

- [ ] Import do service adicionado
- [ ] Service injetado em `__init__`
- [ ] Todos os `with session_scope()` removidos
- [ ] Todas as queries diretas removidas
- [ ] Try/except em volta de chamadas de service
- [ ] `_refresh_data()` chamado após operações CRUD
- [ ] Mensagens de erro virão do service (ValueError, etc)
- [ ] Testado manualmente (criar, ler, atualizar, deletar)
- [ ] Nenhuma linha com `session.query()` remanescente
- [ ] Self.db removido (se houver)

---

## 🧪 Como Testar Após Refatorar

1. **Rodar app**: `python app.py`
2. **Testar CRUD**:
   - Criar novo item
   - Listar (deve aparecer)
   - Editar
   - Deletar
   - Procurar erros no console

3. **Verificar erros**: Se houver exceções, vem do service ✅

---

## 📞 Referências

- Services: `/home/samuel/projects/escala/services/`
- Helpers: `/home/samuel/projects/escala/helpers/`
- Tests: `/home/samuel/projects/escala/tests/`
- SOLID Patterns: `/home/samuel/projects/escala/AGENTS.md`

---

**Pronto para refatorar? Escolha um frame, siga este template, e teste! 🚀**
