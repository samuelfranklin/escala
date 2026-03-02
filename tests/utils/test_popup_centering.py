import unittest

from utils import _calculate_center_position


class PopupCenteringTests(unittest.TestCase):
    def test_calcula_posicao_central_na_tela(self) -> None:
        x, y = _calculate_center_position(500, 400, 1920, 1080)
        self.assertEqual(x, 710)
        self.assertEqual(y, 340)


if __name__ == "__main__":
    unittest.main()
