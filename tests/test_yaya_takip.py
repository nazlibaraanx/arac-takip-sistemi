import unittest

import numpy as np

from yaya_takip import YayaTakip


class YayaTakipTestleri(unittest.TestCase):

    def setUp(self):
        self.kare = np.zeros((100, 100, 3), dtype=np.uint8)

    @staticmethod
    def yaya(y2, takip_id=12, x1=40, x2=50):
        return {
            "id": takip_id,
            "sinif": "Yaya Yolcu",
            "kutu": (x1, y2 - 20, x2, y2),
        }

    def test_iki_cizgiyi_gecen_yaya_yalnizca_bir_kez_sayilir(self):
        takip = YayaTakip(min_gorulme=3)
        self.assertEqual(takip.guncelle([self.yaya(45)], self.kare), [])
        self.assertEqual(takip.guncelle([self.yaya(58)], self.kare), [])
        tamamlanan = self.yaya(72)
        self.assertEqual(takip.guncelle([tamamlanan], self.kare), [tamamlanan])
        self.assertEqual(takip.guncelle([self.yaya(80)], self.kare), [])
        self.assertEqual(takip.toplam_yaya, 1)

    def test_farkli_yaya_idleri_ayri_sayilir(self):
        takip = YayaTakip(min_gorulme=2)
        takip.guncelle([self.yaya(45, 1), self.yaya(45, 2)], self.kare)
        takip.guncelle([self.yaya(58, 1), self.yaya(58, 2)], self.kare)
        yeni = takip.guncelle(
            [self.yaya(72, 1), self.yaya(72, 2)],
            self.kare,
        )

        self.assertEqual([yaya["id"] for yaya in yeni], [1, 2])
        self.assertEqual(takip.toplam_yaya, 2)

    def test_cizgileri_gecmeyen_yaya_sayilmaz(self):
        takip = YayaTakip(min_gorulme=2)
        for y2 in (40, 42, 44, 46):
            self.assertEqual(
                takip.guncelle([self.yaya(y2)], self.kare),
                [],
            )
        self.assertEqual(takip.toplam_yaya, 0)

    def test_gecis_alani_disindaki_yaya_sayilmaz(self):
        takip = YayaTakip(min_gorulme=2)
        for y2 in (45, 58, 72):
            takip.guncelle([self.yaya(y2, x1=5, x2=15)], self.kare)
        self.assertEqual(takip.toplam_yaya, 0)


if __name__ == "__main__":
    unittest.main()
