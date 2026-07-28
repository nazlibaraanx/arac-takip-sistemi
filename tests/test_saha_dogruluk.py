import os
import tempfile
import unittest

from saha_dogruluk import (
    dogruluk_raporu_hesapla,
    saha_csv_oku,
    saha_sablonu_olustur,
)


class SahaDogrulukTestleri(unittest.TestCase):

    def test_arac_ve_yaya_dogrulugu_ayri_hesaplanir(self):
        sonuc = dogruluk_raporu_hesapla([
            {
                "gorevli_arac": 10, "sistem_arac": 9,
                "gorevli_yaya": 20, "sistem_yaya": 18,
            },
            {
                "gorevli_arac": 10, "sistem_arac": 10,
                "gorevli_yaya": 10, "sistem_yaya": 10,
            },
        ])
        self.assertEqual(sonuc["arac"]["dogruluk_yuzdesi"], 95.0)
        self.assertAlmostEqual(
            sonuc["yaya"]["dogruluk_yuzdesi"], 93.3333333333
        )

    def test_saha_sablonu_okunabilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "saha.csv")
            saha_sablonu_olustur(yol)
            self.assertEqual(saha_csv_oku(yol), [])
