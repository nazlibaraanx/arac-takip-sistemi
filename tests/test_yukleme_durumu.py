import os
import tempfile
import unittest

from yukleme_durumu import (
    yukleme_bilgisini_oku,
    yukleme_durumunu_oku,
    yukleme_durumunu_yaz,
)


class YuklemeDurumuTestleri(unittest.TestCase):

    def test_yukleme_durumu_kalici_yazilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "durum.json")
            self.assertTrue(yukleme_durumunu_yaz(True, yol))
            self.assertTrue(yukleme_durumunu_oku(yol))
            self.assertFalse(yukleme_durumunu_yaz(False, yol))
            self.assertFalse(yukleme_durumunu_oku(yol))

    def test_aktif_sefer_numarasi_durumla_birlikte_saklanir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "durum.json")
            yukleme_durumunu_yaz(True, yol, sefer_id=42)
            self.assertEqual(
                yukleme_bilgisini_oku(yol),
                {"aktif": True, "sefer_id": 42},
            )

    def test_dosya_yokken_varsayilan_kullanilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "durum.json")
            self.assertTrue(yukleme_durumunu_oku(yol, varsayilan=True))


if __name__ == "__main__":
    unittest.main()
