import unittest

from egitim.etiketleme_araci import (
    SINIFLAR,
    kutuyu_yolo_satirina_cevir,
    yolo_satirini_kutuya_cevir,
)


class EtiketlemeAraciTestleri(unittest.TestCase):

    def test_feribot_siniflari_beklenen_sirada(self):
        self.assertEqual(
            SINIFLAR,
            [
                "Motosiklet",
                "Çapa",
                "Otomobil",
                "Toplu Taşıma",
                "Traktör Römorklu",
                "Kamyonet",
                "Kamyon",
                "Uzun Araç",
            ],
        )

    def test_kutu_yolo_formatina_cevrilip_geri_okunabilir(self):
        kutu = (3, 100.0, 50.0, 500.0, 400.0)
        satir = kutuyu_yolo_satirina_cevir(kutu, 960, 576)
        sonuc = yolo_satirini_kutuya_cevir(satir, 960, 576)

        self.assertIsNotNone(sonuc)
        self.assertEqual(sonuc[0], kutu[0])
        for beklenen, gercek in zip(kutu[1:], sonuc[1:]):
            self.assertAlmostEqual(gercek, beklenen, places=3)

    def test_gecersiz_etiket_satirlari_atlanir(self):
        self.assertIsNone(yolo_satirini_kutuya_cevir("bozuk satır", 960, 576))
        self.assertIsNone(yolo_satirini_kutuya_cevir("99 0.5 0.5 0.2 0.2", 960, 576))


if __name__ == "__main__":
    unittest.main()
