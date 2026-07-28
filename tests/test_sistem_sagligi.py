import tempfile
import unittest

import numpy as np

from sistem_sagligi import SistemSagligi


class SahteZaman:
    def __init__(self):
        self.deger = 0.0

    def __call__(self):
        return self.deger


class SistemSagligiTestleri(unittest.TestCase):

    def test_ayni_kare_surekli_gelirse_donma_uyarisi_verir(self):
        zaman = SahteZaman()
        with tempfile.TemporaryDirectory() as klasor:
            saglik = SistemSagligi(
                klasor, donma_suresi=5, zaman_fonksiyonu=zaman
            )
            kare = np.zeros((40, 40, 3), dtype=np.uint8)
            self.assertIsNone(saglik.kareyi_kontrol_et(kare))
            zaman.deger = 6
            self.assertIn("donmuş", saglik.kareyi_kontrol_et(kare))

    def test_kare_degisiminde_donma_sayaci_sifirlanir(self):
        zaman = SahteZaman()
        with tempfile.TemporaryDirectory() as klasor:
            saglik = SistemSagligi(
                klasor, donma_suresi=5, zaman_fonksiyonu=zaman
            )
            saglik.kareyi_kontrol_et(
                np.zeros((40, 40, 3), dtype=np.uint8)
            )
            zaman.deger = 4
            self.assertIsNone(saglik.kareyi_kontrol_et(
                np.ones((40, 40, 3), dtype=np.uint8) * 255
            ))
