import importlib.util
import sys
import types
import unittest


if importlib.util.find_spec("cv2") is None:
    sys.modules["cv2"] = types.SimpleNamespace()

from gecis_kontrol import GecisKontrol


class SahteKare:
    shape = (1000, 1000, 3)


class GecisKontrolTestleri(unittest.TestCase):

    @staticmethod
    def arac(arac_id, alt_y):
        return {
            "id": arac_id,
            "sinif": "Otomobil",
            "kutu": (400, alt_y - 100, 600, alt_y)
        }

    def test_arac_iki_cizgiyi_gecince_bir_kez_sayilir(self):
        kontrol = GecisKontrol()
        kare = SahteKare()

        self.assertEqual(
            kontrol.araclari_kontrol_et([self.arac(7, 500)], kare),
            []
        )
        self.assertEqual(
            kontrol.araclari_kontrol_et([self.arac(7, 560)], kare),
            []
        )

        tamamlananlar = kontrol.araclari_kontrol_et(
            [self.arac(7, 720)],
            kare
        )

        self.assertEqual([kayit["id"] for kayit in tamamlananlar], [7])
        self.assertEqual(kontrol.toplam_gecen_arac, 1)

        tekrar = kontrol.araclari_kontrol_et([self.arac(7, 760)], kare)
        self.assertEqual(tekrar, [])
        self.assertEqual(kontrol.toplam_gecen_arac, 1)

    def test_tamamlanan_id_zaman_asimindan_sonra_tekrar_sayilmaz(self):
        kontrol = GecisKontrol()
        kare = SahteKare()

        kontrol.araclari_kontrol_et([self.arac(7, 500)], kare)
        kontrol.araclari_kontrol_et([self.arac(7, 560)], kare)
        kontrol.araclari_kontrol_et([self.arac(7, 720)], kare)
        son_gorulme = kontrol.arac_durumlari[7]["son_gorulme"]

        kontrol.eski_araclari_temizle(
            son_gorulme + kontrol.tamamlanan_arac_silme_suresi + 1
        )
        self.assertNotIn(7, kontrol.arac_durumlari)
        self.assertIn(7, kontrol.tamamlanan_araclar)

        kontrol.araclari_kontrol_et([self.arac(7, 500)], kare)
        kontrol.araclari_kontrol_et([self.arac(7, 560)], kare)
        tekrar = kontrol.araclari_kontrol_et([self.arac(7, 720)], kare)

        self.assertEqual(tekrar, [])
        self.assertEqual(kontrol.toplam_gecen_arac, 1)

    def test_ters_yondeki_arac_sayilmaz(self):
        kontrol = GecisKontrol()
        kare = SahteKare()

        kontrol.araclari_kontrol_et([self.arac(8, 750)], kare)
        kontrol.araclari_kontrol_et([self.arac(8, 500)], kare)

        self.assertEqual(kontrol.toplam_gecen_arac, 0)

    def test_gecis_cizgileri_daraltilip_saga_kaydirilmistir(self):
        kontrol = GecisKontrol()

        giris_sol, giris_sag, bitis_sol, bitis_sag = (
            kontrol.noktalari_hesapla(SahteKare())
        )

        self.assertEqual((giris_sol[0], giris_sag[0]), (380, 900))
        self.assertEqual((bitis_sol[0], bitis_sag[0]), (380, 900))


if __name__ == "__main__":
    unittest.main()
