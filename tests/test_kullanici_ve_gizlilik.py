import os
import tempfile
import unittest
from datetime import datetime

from kullanici_yonetimi import KullaniciYonetimi
from veritabani import Veritabani


class KullaniciVeGizlilikTestleri(unittest.TestCase):

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.vt = Veritabani(os.path.join(self.klasor.name, "test.db"))

    def tearDown(self):
        self.vt.baglantiyi_kapat()
        self.klasor.cleanup()

    def test_sifre_ozetli_saklanir_ve_dogru_sifreyle_girilir(self):
        yonetim = KullaniciYonetimi(self.vt)
        yonetim.kullanici_olustur("yonetici", "GucluSifre123", "Yönetici")
        self.vt.imlec.execute(
            "SELECT sifre_ozeti FROM kullanicilar WHERE kullanici_adi=?",
            ("yonetici",),
        )
        self.assertNotEqual(self.vt.imlec.fetchone()[0], "GucluSifre123")
        self.assertEqual(
            yonetim.giris_yap("yonetici", "GucluSifre123")["rol"],
            "Yönetici",
        )
        self.assertIsNone(yonetim.giris_yap("yonetici", "yanlis"))

    def test_eski_plaka_sayimlari_bozmadan_maskelenir(self):
        self.vt.gecis_kaydet(1, "44ABC123", "Otomobil", 180, 240)
        self.vt.imlec.execute(
            "UPDATE gecisler SET tarih='01.01.2026'"
        )
        self.vt.baglanti.commit()
        adet = self.vt.eski_plakalari_maskele(
            90, simdi=datetime(2026, 7, 27)
        )
        self.assertEqual(adet, 1)
        self.assertEqual(self.vt.gecis_ozetlerini_getir()[0][3], "SİLİNDİ")
        self.assertEqual(self.vt.toplam_arac_sayisi(), 1)

    def test_onemli_islemler_denetim_kaydina_yazilir(self):
        self.vt.denetim_kaydi_ekle("gorevli", "Yükleme başlatıldı", "SF-1")
        kayit = self.vt.denetim_kayitlarini_getir(1)[0]
        self.assertEqual(kayit[1:], ("gorevli", "Yükleme başlatıldı", "SF-1"))
