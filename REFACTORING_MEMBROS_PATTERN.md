# 📚 Guia de Refatoração Aplicada - MembrosFrame

Este documento mostra os **padrões exatos** aplicados durante a refatoração de `gui/membros.py` → `MembrosService`.

---

## 🎯 Princípio Central

> **Thin GUI, Thick Service**
> 
> - GUI: Apenas apresentação + orquestração
> - Service: Validação + persistência + lógica

---

## 📋 Padrões Aplicados

### Padrão 1: Injeção de Service

**Antes:**
```python
class MembrosFrame(ttk.Frame):
    def __init__(self, parent, db=None):
        super().__init__(parent)
        self.db = db  # ❌ Misturado com GUI
        # ... queries diretas quando necessário ...
```

**Depois:**
```python
class MembrosFrame(ttk.Frame):
    def __init__(self, parent, db=None):
        super().__init__(parent)
        self.service = MembrosService()  # ✅ Injeção clara
        self.db = db  # backward compat (removível)
```

---

### Padrão 2: Substituição de Query Direta

**Antes:**
```python
def _on_select(self, _event=None) -> None:
    # ...
    with session_scope() as session:
        todos = session.query(Squad).order_by(Squad.nome).all()
    # ...
```

**Depois:**
```python
def _on_select(self, _event=None) -> None:
    # ...
    todos = self.service.get_all_squads()  # ✅ Service chama query
    # ...
```

**Razão:** Service centraliza lógica BD, GUI fica clean.

---

### Padrão 3: Try/Except em Operações

**Antes:**
```python
def adicionar(self) -> None:
    dlg = MembroDialog(self, self.patentes)
    if not dlg.result:
        return
    
    nome, email, telefone, _, _, _ = dlg.result
    try:
        with session_scope() as session:
            existe = session.query(Member)...
            novo = Member(...)
            session.add(novo)
            session.commit()
```

**Depois:**
```python
def adicionar(self) -> None:
    dlg = MembroDialog(self, self.patentes)
    if not dlg.result:
        return
    
    nome, email, telefone, _, _, _ = dlg.result
    try:
        # ✅ Service cuida de validação + persistência
        self.service.create_member(
            name=nome,
            email=email or None,
            phone_number=telefone or None
        )
        messagebox.showinfo("Sucesso", "Membro criado!")
        self.atualizar_lista()
    except ValueError as e:
        messagebox.showerror("Erro", str(e))
```

**Razão:** Erro tratado uma vez no service, não em múltiplos lugares.

---

### Padrão 4: Operações CRUD Padrão

Todas as operações CRUD seguem este padrão:

```
┌──────────────────────────────────────┐
│ GUI (apresentação + orquestração)    │
└──────────────┬───────────────────────┘
               │ try:
               ▼
┌──────────────────────────────────────┐
│ Service (validação + persistência)   │
│  - validate input                    │
│  - query database                    │
│  - commit transaction                │
│  - return result/error               │
└──────────────┬───────────────────────┘
               │ except ValueError:
               ▼
┌──────────────────────────────────────┐
│ GUI (messagebox.showerror)          │
└──────────────────────────────────────┘
```

---

## 🔄 Exemplos de Refatoração

### Exemplo 1: Listar Membros

```python
# ANTES (múltiplas linhas, lógica misturada):
def atualizar_lista(self) -> None:
    for item in self.tree_membros.get_children():
        self.tree_membros.delete(item)

    try:
        with session_scope() as session:
            members = session.query(Member).filter_by(status=True).order_by(Member.name).all()
        
        for idx, member in enumerate(members):
            squads_list = [ms.squad.nome for ms in member.memberships]
            times_str = ", ".join(squads_list)
            tag = "odd" if idx % 2 == 0 else "even"
            self.tree_membros.insert("", "end", iid=member.id, 
                                    values=(member.name, member.phone_number or "", times_str),
                                    tags=(tag,))
        total = len(members)
        self._lbl_count.config(text=f"({total}...)")
    except Exception as e:
        messagebox.showerror("Erro ao carregar membros", str(e))

# DEPOIS (clean, service isolado):
def atualizar_lista(self) -> None:
    for item in self.tree_membros.get_children():
        self.tree_membros.delete(item)

    try:
        members = self.service.get_all_members()  # ✅ Service call
        
        for idx, member in enumerate(members):
            squads_list = [ms.squad.nome for ms in member.memberships]
            times_str = ", ".join(squads_list)
            tag = "odd" if idx % 2 == 0 else "even"
            self.tree_membros.insert("", "end", iid=member.id,
                                    values=(member.name, member.phone_number or "", times_str),
                                    tags=(tag,))
        total = len(members)
        self._lbl_count.config(text=f"({total}...)")
    except Exception as e:
        messagebox.showerror("Erro ao carregar membros", str(e))
```

**Mudanças:**
- ❌ `with session_scope() as session:`
- ✅ `members = self.service.get_all_members()`

---

### Exemplo 2: Criar Membro

```python
# ANTES:
def adicionar(self) -> None:
    dlg = MembroDialog(self, self.patentes)
    if not dlg.result:
        return

    nome, email, telefone, patente, data_entrada, obs = dlg.result
    if not nome:
        messagebox.showerror("Erro", "Nome obrigatório")
        return
    
    try:
        with session_scope() as session:
            existe = session.query(Member).filter(Member.name == nome).first()
            if existe:
                messagebox.showerror("Erro", "Já existe")
                return
            
            novo = Member(name=nome, email=email, phone_number=telefone, status=True)
            session.add(novo)
            session.commit()
            messagebox.showinfo("Sucesso", "Criado!")
            self.atualizar_lista()
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# DEPOIS:
def adicionar(self) -> None:
    dlg = MembroDialog(self, self.patentes)
    if not dlg.result:
        return

    nome, email, telefone, patente, data_entrada, obs = dlg.result
    try:
        # ✅ Service cuida de validação + persistência
        self.service.create_member(
            name=nome,
            email=email or None,
            phone_number=telefone or None,
            instagram=None,
        )
        messagebox.showinfo("Sucesso", "Membro adicionado com sucesso!")
        self.atualizar_lista()
    except ValueError as e:
        messagebox.showerror("Erro ao adicionar membro", str(e))
    except Exception as e:
        messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
```

**Vantagens:**
- ✅ Validação centralizada no service
- ✅ Uma única fonte de verdade para regras
- ✅ Fácil de testar

---

### Exemplo 3: Deletar Membro

```python
# ANTES:
def remover(self) -> None:
    sel = self.tree_membros.selection()
    if not sel:
        messagebox.showwarning("Aviso", "Selecione um membro.")
        return

    membro_id = sel[0]
    
    try:
        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            if not member:
                return
            nome = member.name
    
        if not messagebox.askyesno("Confirmar", f"Remover '{nome}'?"):
            return
        
        with session_scope() as session:
            member = session.query(Member).filter_by(id=membro_id).first()
            member.status = False
            session.commit()
        
        messagebox.showinfo("Sucesso", "Removido!")
        self.atualizar_lista()
    except Exception as e:
        messagebox.showerror("Erro ao remover membro", str(e))

# DEPOIS:
def remover(self) -> None:
    sel = self.tree_membros.selection()
    if not sel:
        messagebox.showwarning("Aviso", "Selecione um membro.")
        return

    membro_id = sel[0]

    try:
        member = self.service.get_member_by_id(membro_id)  # ✅
        if not member:
            return
        nome = member.name
    except Exception as e:
        messagebox.showerror("Erro ao buscar membro", str(e))
        return

    if not messagebox.askyesno("Confirmar", f"Remover membro '{nome}'?"):
        return

    try:
        success = self.service.delete_member(membro_id)  # ✅
        if success:
            messagebox.showinfo("Sucesso", "Membro removido com sucesso!")
            self.atualizar_lista()
        else:
            messagebox.showerror("Erro", "Falha ao remover membro.")
    except Exception as e:
        messagebox.showerror("Erro ao remover membro", str(e))
```

**Benefícios:**
- ✅ Lógica de soft delete no service
- ✅ GUI apenas orquestra
- ✅ Testável sem BD real

---

### Exemplo 4: Squad Assignment (NEW)

```python
def salvar_squads(self) -> None:
    if not self._membro_selecionado:
        messagebox.showwarning("Aviso", "Selecione um membro primeiro.")
        return

    membro_id = self._membro_selecionado

    try:
        # ✅ Service busca estado atual
        member = self.service.get_member_by_id(membro_id)
        if not member:
            messagebox.showerror("Erro", "Membro não encontrado.")
            return

        current_squads = {ms.squad_id for ms in member.memberships}
        
        # ✅ Processa cada squad com service
        errors = []
        for squad_id, (var_check, var_patente) in self.squads_widgets.items():
            is_checked = var_check.get()
            try:
                patente_str = var_patente.get()
                level = int(patente_str)
            except (ValueError, TypeError):
                level = 1
            
            # ✅ Atender novo squad
            if is_checked and squad_id not in current_squads:
                result = self.service.assign_member_to_squad(
                    member_id=membro_id,
                    squad_id=squad_id,
                    level=level
                )
                if result is None:
                    errors.append(f"Erro ao adicionar {squad_id}")
            
            # ✅ Remover de squad
            elif not is_checked and squad_id in current_squads:
                success = self.service.remove_member_from_squad(
                    member_id=membro_id,
                    squad_id=squad_id
                )
                if not success:
                    errors.append(f"Erro ao remover {squad_id}")
        
        if errors:
            messagebox.showwarning("Aviso", f"Erros ao salvar:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Sucesso", "Times salvos com sucesso!")
        
        self.atualizar_lista()
    except Exception as e:
        messagebox.showerror("Erro ao salvar times", str(e))
```

**Padrão:**
1. Busca estado atual via service
2. Processa mudanças via service
3. Agrupa erros
4. Mostra resultado ao usuário

---

## 🧪 Padrão de Testes

### Teste de Service Call

```python
def test_atualizar_lista_calls_service(self):
    """Verify that atualizar_lista uses MembrosService.get_all_members()."""
    frame = MembrosFrame(self.root, db=None)
    
    # ✅ Mock service
    frame.service.get_all_members = Mock(return_value=[])
    
    # ✅ Call method
    frame.atualizar_lista()
    
    # ✅ Verify service was called
    frame.service.get_all_members.assert_called_once()
```

### Teste de Dialog + Service

```python
@patch('gui.membros.MembroDialog')
def test_create_membro_via_gui(self, mock_dialog_class):
    """Verify that adicionar() calls MembrosService.create_member()."""
    frame = MembrosFrame(self.root, db=None)
    
    # ✅ Mock dialog
    mock_dialog_instance = Mock()
    mock_dialog_instance.result = ("João", "joao@test.com", "123", "Recruta", "", "")
    mock_dialog_class.return_value = mock_dialog_instance
    
    # ✅ Mock service
    frame.service.create_member = Mock(return_value=Mock(spec=Member))
    frame.atualizar_lista = Mock()
    
    # ✅ Call method
    frame.adicionar()
    
    # ✅ Verify service was called with correct params
    frame.service.create_member.assert_called_once()
    call_args = frame.service.create_member.call_args
    self.assertEqual(call_args[1]['name'], "João")
    self.assertEqual(call_args[1]['email'], "joao@test.com")
```

---

## 📊 Resumo de Mudanças

| Aspecto | Antes | Depois |
|--------|-------|--------|
| **session_scope() em GUI** | Múltiplos | 0 ✅ |
| **Queries diretas** | Cliente/UI mesclado | Service isolado |
| **Validação** | Dispersa (UI + BD) | Centralizada (Service) |
| **Erro handling** | Repetiido em todo lugar | Centralizado (Service) |
| **Testabilidade** | Difícil (dependência real) | Fácil (mock service) |
| **Manutenção** | Frágil (múltiplas fontes) | Robusto (fonte única) |

---

## ✅ Resultado

```
gui/membros.py
├── ✅ Thin (apresentação + orquestração)
├── ✅ Clean (sem queries diretas)
├── ✅ Testável (mock service)
└── ✅ Manuível (lógica centralizada)

services/membros_service.py
├── ✅ Thick (validação + persistência)
├── ✅ Isolado (session_scope interno)
├── ✅ Reutilizável (múltiplos contextos)
└── ✅ 100% testado (helpers coverage)
```

Este é o **arquétipo** a seguir para refatorar outros frames!
