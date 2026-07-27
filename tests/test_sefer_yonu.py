import os
import tempfile
import unittest

from sefer_yonu import (
    BASKIL_MALATYA,
    MALATYA_BASKIL,
    sefer_yonunu_oku,
    sefer_yonunu_yaz,
    ters_sefer_yonu,
)


class SeferYonuTestleri(unittest.TestCase):

    def test_iki_yon_ayri_kaydedilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "yon.json")
            sefer_yonunu_yaz(BASKIL_MALATYA, yol)
            self.assertEqual(sefer_yonunu_oku(yol), BASKIL_MALATYA)
            sefer_yonunu_yaz(MALATYA_BASKIL, yol)
            self.assertEqual(sefer_yonunu_oku(yol), MALATYA_BASKIL)

    def test_sefer_bittiginde_siradaki_yon_tersidir(self):
        self.assertEqual(ters_sefer_yonu(MALATYA_BASKIL), BASKIL_MALATYA)
        self.assertEqual(ters_sefer_yonu(BASKIL_MALATYA), MALATYA_BASKIL)


if __name__ == "__main__":
    unittest.main()
