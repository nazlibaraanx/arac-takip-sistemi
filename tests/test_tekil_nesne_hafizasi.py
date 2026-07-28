import unittest

import numpy as np

from tekil_nesne_hafizasi import TekilNesneHafizasi


class TekilNesneHafizasiTestleri(unittest.TestCase):

    def setUp(self):
        self.hafiza = TekilNesneHafizasi()
        self.kutu = (10, 10, 90, 90)

    @staticmethod
    def kare_olustur(renk, desen=False):
        kare = np.zeros((100, 100, 3), dtype=np.uint8)
        kare[10:90, 10:90] = renk
        if desen:
            kare[25:45, 25:75] = (255, 255, 255)
        return kare

    def test_ayni_gorunum_yeni_takip_kimliginde_mukerrer_sayilir(self):
        kare = self.kare_olustur((30, 80, 180), desen=True)
        self.hafiza.kaydet(
            "arac", kare, self.kutu, etiket="Otomobil"
        )

        self.assertTrue(
            self.hafiza.daha_once_sayildi_mi(
                "arac", kare.copy(), self.kutu, etiket="Otomobil"
            )
        )

    def test_farkli_gorunum_ayri_nesne_sayilir(self):
        ilk = self.kare_olustur((20, 30, 180), desen=True)
        ikinci = self.kare_olustur((180, 30, 20), desen=False)
        self.hafiza.kaydet(
            "arac", ilk, self.kutu, etiket="Otomobil"
        )

        self.assertFalse(
            self.hafiza.daha_once_sayildi_mi(
                "arac", ikinci, self.kutu, etiket="Otomobil"
            )
        )

    def test_ayni_okunmus_plaka_gorunumden_bagimsiz_engellenir(self):
        self.hafiza.plakalari_yukle(["44 ABC 123"])
        farkli_arac = self.kare_olustur((10, 220, 10))

        self.assertTrue(
            self.hafiza.daha_once_sayildi_mi(
                "arac",
                farkli_arac,
                self.kutu,
                etiket="Otomobil",
                plaka="44ABC123",
            )
        )

    def test_hafiza_sifirlaninca_onceki_nesne_unutulur(self):
        kare = self.kare_olustur((30, 80, 180), desen=True)
        self.hafiza.kaydet(
            "yaya", kare, self.kutu, etiket="Yaya Yolcu"
        )
        self.hafiza.sifirla()

        self.assertFalse(
            self.hafiza.daha_once_sayildi_mi(
                "yaya", kare, self.kutu, etiket="Yaya Yolcu"
            )
        )


if __name__ == "__main__":
    unittest.main()
