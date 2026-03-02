# 📚 Guia de Documentação - Índice

Bem-vindo ao diretório de guidelines do projeto **Escala**. Aqui você encontra toda a documentação relacionada à refatoração e arquitetura do projeto.

---

## 📖 Documentos Disponíveis

### 🚀 Começar Aqui
- **[QUICKSTART_PHASE2.md](QUICKSTART_PHASE2.md)** - TL;DR: 5 minutos para começar a refatorar a GUI
  - Template pronto para copiar
  - Quick reference de services
  - Checklist de refatoração

### 📊 Visão Geral
- **[PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md)** - Status final da Fase 1
  - Métricas de cobertura
  - Padrões implementados
  - Próximos passos
  
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Resumo completo da refatoração
  - 7 módulos refatorados
  - Antes vs. Depois
  - Benefícios alcançados

### 🏗️ Arquitetura e Padrões
- **[REFACTOR_PLAN.md](REFACTOR_PLAN.md)** - Plano detalhado de refatoração
  - Estrutura de diretórios
  - Módulos e dependências
  - Workflow TDD

### 🎯 Guias de Refatoração
- **[GUI_REFACTORING_GUIDE.md](GUI_REFACTORING_GUIDE.md)** - Guia passo-a-passo para refatorar GUI
  - Padrão: Antes vs. Depois
  - Exemplo completo (Membros)
  - Checklist detalhado
  - Referência de Services
  - Troubleshooting

### 🔬 Deep Dives por Módulo
- **[REFACTORING_ESCALA_GENERATOR.md](REFACTORING_ESCALA_GENERATOR.md)** - Deep dive do algoritmo de geração
  - Lógica extraída
  - Padrões SOLID
  - Cobertura de testes

- **[REFACTORING_DISPONIBILIDADE.md](REFACTORING_DISPONIBILIDADE.md)** - Deep dive de disponibilidade
  - Validações implementadas
  - Restrições de data
  - Cobertura de testes

- **[REFACTORING_VISUALIZAR_SUMMARY.md](REFACTORING_VISUALIZAR_SUMMARY.md)** - Deep dive de visualização
  - Funções de filtro
  - Exportação CSV
  - Cobertura de testes

---

## 🎓 Como Usar Esta Documentação

### Se você é novo no projeto:
1. Leia [PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md) para entender o contexto
2. Leia [REFACTOR_PLAN.md](REFACTOR_PLAN.md) para entender a arquitetura
3. Comece com [QUICKSTART_PHASE2.md](QUICKSTART_PHASE2.md) para primeira refatoração

### Se quer refatorar a GUI:
1. Leia [QUICKSTART_PHASE2.md](QUICKSTART_PHASE2.md) (5 min)
2. Consulte [GUI_REFACTORING_GUIDE.md](GUI_REFACTORING_GUIDE.md) para detalhes
3. Use checklist como referência

### Se quer entender um módulo específico:
- **Casais**: Consulte [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md#casais)
- **Membros**: Consulte [GUI_REFACTORING_GUIDE.md](GUI_REFACTORING_GUIDE.md#exemplo-completo-refatorar-membrosframe)
- **Escala**: Consulte [REFACTORING_ESCALA_GENERATOR.md](REFACTORING_ESCALA_GENERATOR.md)
- **Disponibilidade**: Consulte [REFACTORING_DISPONIBILIDADE.md](REFACTORING_DISPONIBILIDADE.md)

---

## 📊 Estrutura do Projeto (Refatorado)

```
project/
├── guidelines/              ← Você está aqui
│   └── *.md                (documentação deste projeto)
├── helpers/                 ← Lógica pura (testável)
├── services/                ← Orquestra BD + helpers
├── tests/
│   ├── helpers/            ← Testes de funções puras
│   ├── services/           ← Testes de serviços
│   ├── integration/        ← Testes de integração
│   └── utils/              ← Testes de utilidades
├── gui/                     ← Frames Tkinter (thin layer)
├── infra/                   ← BD (SQLAlchemy)
└── docs/                    ← Referências externas
```

---

## 🔗 Links Importantes

- **Database**: `/infra/database.py` - Modelos SQLAlchemy
- **Services**: `/services/` - Camada de aplicação
- **Helpers**: `/helpers/` - Lógica de negócio
- **Tests**: `/tests/` - Suite de testes

---

## ✅ Checklist de Leitura

- [ ] Li [QUICKSTART_PHASE2.md](QUICKSTART_PHASE2.md)
- [ ] Li [REFACTOR_PLAN.md](REFACTOR_PLAN.md)
- [ ] Li [GUI_REFACTORING_GUIDE.md](GUI_REFACTORING_GUIDE.md)
- [ ] Entendo a arquitetura (Helpers → Services → GUI)
- [ ] Estou pronto para refatorar um frame

---

## 💬 Dúvidas Frequentes

**P: Onde começo?**  
R: [QUICKSTART_PHASE2.md](QUICKSTART_PHASE2.md) tem TL;DR de 5 minutos.

**P: Como refatoro a GUI?**  
R: Siga [GUI_REFACTORING_GUIDE.md](GUI_REFACTORING_GUIDE.md) com o template passo-a-passo.

**P: Como funcionam os services?**  
R: Veja seção "Referência Rápida de Services" em [QUICKSTART_PHASE2.md](QUICKSTART_PHASE2.md).

**P: Quais são os padrões do projeto?**  
R: Leia [REFACTOR_PLAN.md](REFACTOR_PLAN.md) - seção "Padrões a Seguir".

**P: Por que a lógica está separada?**  
R: [PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md) explica os benefícios.

---

## 🎯 Objetivo Final

Transformar o projeto de uma massa de código sem testes para:
- ✅ Lógica pura e reutilizável
- ✅ 300+ testes automatizados
- ✅ 98% cobertura
- ✅ SOLID principles
- ✅ Arquitetura clara

**Status**: Fase 1 completa ✅ | Fase 2 (GUI) em progresso 🚀

---

*Última atualização: 2 de março de 2026*
