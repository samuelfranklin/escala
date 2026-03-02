"""
Testes de integração para DisponibilidadeFrame.

Valida que:
1. Frame foi refatorado para usar DisponibilidadeService
2. CRUD de restrições funciona corretamente via GUI
3. Erro handling é apropriado para datas inválidas
"""

import tkinter as tk
import unittest
from datetime import date, timedelta
import tempfile
import os

# Setup de DB temporária ANTES de importar qualquer coisa
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
temp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"

from gui.disponibilidade_orm import DisponibilidadeFrame
from services.disponibilidade_service import DisponibilidadeService
from services.membros_service import MembrosService
from infra.database import Member, session_scope, create_tables


class TestDisponibilidadeFrameIntegration(unittest.TestCase):
    """Testes de integração: Frame + Service + BD"""

    @classmethod
    def setUpClass(cls):
        """Cria schema uma vez."""
        create_tables()

    def setUp(self):
        """Cria membros de teste locais."""
        # Clear all members first
        with session_scope() as session:
            session.query(Member).delete()
            members = [
                Member(name="João Silva"),
                Member(name="Maria Santos"),
                Member(name="Pedro Oliveira"),
            ]
            session.add_all(members)

        # Cria janela raiz e frame para teste
        self.root = tk.Tk()
        self.root.withdraw()  # Oculta janela
        self.frame = DisponibilidadeFrame(self.root)
        self.frame.pack()
        self.root.update()

    def tearDown(self):
        """Limpa após cada teste."""
        try:
            self.root.destroy()
        except:
            pass

    # ===== TESTES OBRIGATÓRIOS =====

    def test_1_disponibilidade_frame_initializes(self):
        """✅ TEST 1: Frame inicializa com DisponibilidadeService e MembrosService."""
        self.assertIsNotNone(self.frame.service, "Frame deve ter DisponibilidadeService")
        self.assertIsInstance(self.frame.service, DisponibilidadeService, 
                              "service deve ser DisponibilidadeService")
        self.assertIsNotNone(self.frame.membros_service, "Frame deve ter MembrosService")
        self.assertIsInstance(self.frame.membros_service, MembrosService,
                              "membros_service deve ser MembrosService")
        self.assertIsNotNone(self.frame.combo_membros, "combo_membros deve existir")
        self.assertIsNotNone(self.frame.tree_restricoes, "tree_restricoes deve existir")

    def test_2_add_restriction_via_gui(self):
        """✅ TEST 2: Restrição criada via UI é salva no BD."""
        # Seleciona membro
        self.frame.combo_membros.set("João Silva")
        self.frame._on_membro_selected()
        self.root.update()

        # Insere dados
        amanha = date.today() + timedelta(days=1)
        self.frame.entry_data.insert(0, amanha.strftime("%d/%m/%Y"))
        self.frame.entry_descricao.insert(0, "Férias")

        # Simula clique no botão
        self.frame._add_restricao()
        self.root.update()

        # Valida que restrição foi adicionada na treeview
        items = self.frame.tree_restricoes.get_children()
        self.assertGreater(len(items), 0, "Treeview deve ter restrição após add")

        # Valida que foi salva no BD
        restricoes = self.frame.service.get_restrictions_by_member(
            self.frame.membro_atual_id
        )
        self.assertGreater(len(restricoes), 0, "BD deve ter restrição")
        self.assertEqual(
            restricoes[0]["date_display"],
            amanha.strftime("%d/%m/%Y"),
            "Data deve estar correta"
        )

    def test_3_restricoes_carregam_na_treeview(self):
        """✅ TEST 3: Restrições existentes carregam quando membro é selecionado."""
        # Cria restrição manualmente no BD
        membro_id = None
        with session_scope() as session:
            membro = session.query(Member).filter(
                Member.name == "Maria Santos"
            ).first()
            membro_id = membro.id

        amanha = date.today() + timedelta(days=1)
        result = self.frame.service.create_restriction(
            membro_id,
            amanha.strftime("%d/%m/%Y"),
            "Treinamento"
        )
        self.assertTrue(result["success"], f"Falhou criar restriction: {result['message']}")

        # Seleciona membro na UI
        self.frame.combo_membros.set("Maria Santos")
        self.frame._on_membro_selected()
        self.root.update()

        # Valida que restrição aparece na treeview
        items = self.frame.tree_restricoes.get_children()
        self.assertGreater(len(items), 0, "Treeview deve conter restrições")

        # Valida conteúdo
        item_values = self.frame.tree_restricoes.item(items[0])["values"]
        self.assertEqual(item_values[0], amanha.strftime("%d/%m/%Y"))
        self.assertEqual(item_values[1], "Treinamento")

    def test_4_remove_restriction_via_gui(self):
        """✅ TEST 4: Restrição removida via UI é deletada do BD."""
        # Setup: cria restrição
        self.frame.combo_membros.set("Pedro Oliveira")
        self.frame._on_membro_selected()
        self.root.update()

        amanha = date.today() + timedelta(days=1)
        self.frame.entry_data.insert(0, amanha.strftime("%d/%m/%Y"))
        self.frame.entry_descricao.insert(0, "Licença")
        self.frame._add_restricao()
        self.root.update()

        # Carrega treeview
        items = self.frame.tree_restricoes.get_children()
        self.assertGreater(len(items), 0, "Deve ter adicionado uma restrição")

        # Simula seleção e remoção
        item_id = items[0]
        self.frame.tree_restricoes.selection_set(item_id)

        # Mock: substitui askyesno para retornar True automaticamente
        import tkinter.messagebox as mb
        original_askyesno = mb.askyesno
        mb.askyesno = lambda *args, **kwargs: True

        try:
            self.frame._remove_restricao()
            self.root.update()

            # Valida que foi removido da treeview
            items_after = self.frame.tree_restricoes.get_children()
            self.assertEqual(len(items_after), 0, "Treeview deve estar vazia após remove")

            # Valida que foi removido do BD
            restricoes = self.frame.service.get_restrictions_by_member(
                self.frame.membro_atual_id
            )
            self.assertEqual(len(restricoes), 0, "BD deve estar sem restrições")

        finally:
            mb.askyesno = original_askyesno

    def test_5_error_handling_invalid_date(self):
        """✅ TEST 5: Data inválida exibe erro apropriado."""
        self.frame.combo_membros.set("João Silva")
        self.frame._on_membro_selected()
        self.root.update()

        # Insere data inválida
        self.frame.entry_data.insert(0, "32/13/2026")  # Data impossível
        self.frame.entry_descricao.insert(0, "Teste")

        # Captura mensagem de erro
        import tkinter.messagebox as mb
        error_shown = []
        original_showerror = mb.showerror

        def mock_showerror(title, message, **kwargs):
            error_shown.append((title, message))
            return None

        mb.showerror = mock_showerror

        try:
            self.frame._add_restricao()
            self.root.update()

            # Valida que erro foi exibido
            self.assertGreater(
                len(error_shown),
                0,
                "Deve ter exibido erro para data inválida"
            )

            # Valida que nada foi adicionado
            items = self.frame.tree_restricoes.get_children()
            self.assertEqual(len(items), 0, "Nada deve ser adicionado com erro")

        finally:
            mb.showerror = original_showerror

    def test_service_integration(self):
        """Testa que o service está sendo usado corretamente."""
        # Verifica que service existe e é acessível
        self.assertIsNotNone(self.frame.service)
        
        # Testa que service pode criar restrição
        membro_id = None
        with session_scope() as session:
            membro = session.query(Member).filter(
                Member.name == "João Silva"
            ).first()
            membro_id = membro.id
        
        amanha = date.today() + timedelta(days=1)
        result = self.frame.service.create_restriction(
            membro_id,
            amanha.strftime("%d/%m/%Y"),
            "Test"
        )
        self.assertTrue(result["success"])
        
        # Testa que service pode recuperar restrição
        restricoes = self.frame.service.get_restrictions_by_member(membro_id)
        self.assertGreater(len(restricoes), 0)

    def test_6_membros_service_integration(self):
        """✅ TEST 6: Frame usa MembrosService para carregar membros (sem session_scope)."""
        # Verifica que membros foram carregados via service
        self.assertGreater(len(self.frame.membros_dict), 0, "Membros devem estar carregados")
        
        # Valida que combo tem os membros
        combo_values = list(self.frame.combo_membros["values"])
        self.assertEqual(len(combo_values), 3, "Deve ter 3 membros carregados")
        
        # Valida que MembrosService foi usado (não BD direto)
        membros_via_service = self.frame.membros_service.get_all_members()
        self.assertEqual(len(membros_via_service), 3, "Service deve retornar 3 membros")
        
        # Valida que dictzip combina corretamente
        for membro in membros_via_service:
            self.assertIn(membro.name, self.frame.membros_dict,
                         f"Membro {membro.name} deve estar no dict carregado via service")


if __name__ == "__main__":
    unittest.main()

