import unittest

from gui.membros import MembrosFrame


class MembrosFrameContractTests(unittest.TestCase):
    def test_membros_frame_expoe_metodos_acionados_na_ui(self) -> None:
        for method_name in ["adicionar", "editar", "remover", "salvar_squads"]:
            self.assertTrue(hasattr(MembrosFrame, method_name), method_name)
            self.assertTrue(callable(getattr(MembrosFrame, method_name)), method_name)


if __name__ == "__main__":
    unittest.main()
