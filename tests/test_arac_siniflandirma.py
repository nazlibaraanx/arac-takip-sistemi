from collections import defaultdict

import unittest

from arac_siniflandirma import (
    SinifKararHafizasi,
    genis_toplu_tasima_govdesi_mi,
    kararli_sinifi_guncelle,
    otomobil_boyutunda_mi,
    servis_gibi_mi,
    toplu_tasima_duzeltmesi_gerekli_mi,
)


class AracSiniflandirmaTestleri(unittest.TestCase):

    def test_tek_karelik_geometri_sinifi_degistirmez(self):
        hafiza = SinifKararHafizasi()
        sinif, _guven = hafiza.guncelle(
            10,
            "Otomobil",
            "Toplu Taşıma",
            0.82,
            geometrik_kanit=True,
        )
        self.assertEqual(sinif, "Otomobil")

    def test_surekli_geometri_kaniti_sinifi_duzeltir(self):
        hafiza = SinifKararHafizasi()
        for _ in range(10):
            sinif, guven = hafiza.guncelle(
                11,
                "Kamyon",
                "Toplu Taşıma",
                0.78,
                geometrik_kanit=True,
            )
        self.assertEqual(sinif, "Toplu Taşıma")
        self.assertGreater(guven, 0.50)

    def test_geometri_kaniti_kesilirse_seri_bastan_baslar(self):
        hafiza = SinifKararHafizasi(geometrik_onay_adedi=3)
        hafiza.guncelle(12, "Otomobil", "Toplu Taşıma", 0.8, True)
        hafiza.guncelle(12, "Otomobil", "Otomobil", 0.8, False)
        hafiza.guncelle(12, "Otomobil", "Toplu Taşıma", 0.8, True)
        sinif, _guven = hafiza.guncelle(
            12, "Otomobil", "Toplu Taşıma", 0.8, True
        )
        self.assertEqual(sinif, "Otomobil")

    def test_gorseldeki_genis_minibus_toplu_tasima_govdesidir(self):
        self.assertTrue(genis_toplu_tasima_govdesi_mi(
            kutu=(70, 100, 250, 240),
            kare_sekli=(355, 291, 3),
            min_alt_y_orani=0.45,
            min_genislik_orani=0.30,
            maks_boy_en_orani=0.90,
        ))

    def test_normal_otomobil_genis_toplu_tasima_govdesi_degildir(self):
        self.assertFalse(genis_toplu_tasima_govdesi_mi(
            kutu=(616, 349, 826, 560),
            kare_sekli=(576, 960, 3),
            min_alt_y_orani=0.45,
            min_genislik_orani=0.30,
            maks_boy_en_orani=0.90,
        ))

    def test_ilk_aracla_ayni_orandaki_arac_otomobil_boyutundadir(self):
        self.assertTrue(otomobil_boyutunda_mi(
            kutu=(616, 349, 826, 560),
            kare_sekli=(576, 960, 3),
            min_alt_y_orani=0.45,
            min_genislik_orani=0.08,
            maks_genislik_orani=0.30,
            maks_boy_en_orani=1.05,
        ))

    def test_dar_ve_yuksek_arac_otomobil_boyutunda_degildir(self):
        self.assertFalse(otomobil_boyutunda_mi(
            kutu=(760, 300, 900, 560),
            kare_sekli=(576, 960, 3),
            min_alt_y_orani=0.45,
            min_genislik_orani=0.08,
            maks_genislik_orani=0.30,
            maks_boy_en_orani=1.05,
        ))

    def test_gecici_toplu_tasima_tahmini_otomobil_sinifini_degistirmez(self):
        oylar = defaultdict(lambda: defaultdict(float))

        for _ in range(5):
            sonuc = kararli_sinifi_guncelle(
                oylar, 1, "Otomobil", 0.80
            )
        sonuc = kararli_sinifi_guncelle(
            oylar, 1, "Toplu Taşıma", 0.90
        )

        self.assertEqual(sonuc, "Otomobil")

    def test_gercek_toplu_tasima_cogunlukla_kendi_sinifinda_kalir(self):
        oylar = defaultdict(lambda: defaultdict(float))

        for _ in range(4):
            sonuc = kararli_sinifi_guncelle(
                oylar, 2, "Toplu Taşıma", 0.80
            )
        sonuc = kararli_sinifi_guncelle(
            oylar, 2, "Otomobil", 0.70
        )

        self.assertEqual(sonuc, "Toplu Taşıma")

    def test_girise_yaklasan_dar_ve_yuksek_arac_servis_adayidir(self):
        sonuc = servis_gibi_mi(
            kutu=(500, 280, 650, 500),
            kare_sekli=(720, 1280, 3),
            min_alt_y_orani=0.45,
            maks_genislik_orani=0.22,
            min_boy_en_orani=0.90
        )

        self.assertTrue(sonuc)

    def test_genis_arac_servis_adayi_degildir(self):
        sonuc = servis_gibi_mi(
            kutu=(400, 250, 700, 550),
            kare_sekli=(720, 1280, 3),
            min_alt_y_orani=0.45,
            maks_genislik_orani=0.22,
            min_boy_en_orani=0.90
        )

        self.assertFalse(sonuc)

    def test_uzaktaki_kucuk_tespit_servis_adayi_degildir(self):
        sonuc = servis_gibi_mi(
            kutu=(600, 100, 660, 220),
            kare_sekli=(720, 1280, 3),
            min_alt_y_orani=0.45,
            maks_genislik_orani=0.22,
            min_boy_en_orani=0.90
        )

        self.assertFalse(sonuc)

    def test_kameradaki_minibus_boyutlari_toplu_tasima_adayidir(self):
        sonuc = servis_gibi_mi(
            kutu=(90, 20, 340, 270),
            kare_sekli=(360, 1200, 3),
            min_alt_y_orani=0.45,
            maks_genislik_orani=0.22,
            min_boy_en_orani=0.90
        )

        self.assertTrue(sonuc)

    def test_car_denilen_dar_minibus_toplu_tasima_adayidir(self):
        sonuc = toplu_tasima_duzeltmesi_gerekli_mi(
            model_sinifi="car",
            kutu=(762, 369, 960, 566),
            kare_sekli=(576, 960, 3),
            min_alt_y_orani=0.45,
            maks_genislik_orani=0.22,
            min_boy_en_orani=0.90,
            otomobil_maks_genislik_orani=0.21,
        )

        self.assertTrue(sonuc)

    def test_car_denilen_genis_otomobil_toplu_tasima_adayi_degildir(self):
        sonuc = toplu_tasima_duzeltmesi_gerekli_mi(
            model_sinifi="car",
            kutu=(616, 349, 826, 560),
            kare_sekli=(576, 960, 3),
            min_alt_y_orani=0.45,
            maks_genislik_orani=0.22,
            min_boy_en_orani=0.90,
            otomobil_maks_genislik_orani=0.21,
        )

        self.assertFalse(sonuc)


if __name__ == "__main__":
    unittest.main()
