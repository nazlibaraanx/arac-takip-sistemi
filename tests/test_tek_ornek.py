import os
import tempfile
import unittest

from tek_ornek import TekOrnekKilidi


class TekOrnekKilidiTestleri(unittest.TestCase):

    def test_ikinci_kilit_ayni_anda_alinamaz(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "program.lock")
            birinci = TekOrnekKilidi(yol)
            ikinci = TekOrnekKilidi(yol)
            self.assertTrue(birinci.al())
            self.assertFalse(ikinci.al())
            birinci.birak()
            self.assertTrue(ikinci.al())
            ikinci.birak()

    def test_eski_kilit_dosyasi_temizlenir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "program.lock")
            with open(yol, "w", encoding="ascii") as dosya:
                dosya.write("99999999")
            kilit = TekOrnekKilidi(yol)
            self.assertTrue(kilit.al())
            kilit.birak()


if __name__ == "__main__":
    unittest.main()
