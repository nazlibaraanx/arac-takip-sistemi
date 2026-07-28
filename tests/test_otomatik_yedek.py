import os
import sqlite3
import tempfile
import unittest
from datetime import datetime

from otomatik_yedek import OtomatikYedek


class OtomatikYedekTestleri(unittest.TestCase):

    def test_yedek_verileri_tutar_ve_ayni_gun_tek_dosya_olusturur(self):
        with tempfile.TemporaryDirectory() as klasor:
            kaynak = os.path.join(klasor, "kaynak.db")
            yedekler = os.path.join(klasor, "yedekler")
            baglanti = sqlite3.connect(kaynak)
            baglanti.execute("CREATE TABLE kayitlar(deger TEXT)")
            baglanti.execute("INSERT INTO kayitlar VALUES ('korundu')")
            baglanti.commit()

            simdi = datetime(2026, 7, 27, 10, 30)
            ilk = OtomatikYedek.olustur(
                kaynak, yedekler, baglanti=baglanti, simdi=simdi
            )
            ikinci = OtomatikYedek.olustur(
                kaynak, yedekler, baglanti=baglanti, simdi=simdi
            )
            baglanti.execute("INSERT INTO kayitlar VALUES ('sonraki')")
            baglanti.commit()
            OtomatikYedek.olustur(
                kaynak,
                yedekler,
                baglanti=baglanti,
                simdi=simdi,
                zorla=True,
            )
            baglanti.close()

            self.assertEqual(ilk, ikinci)
            self.assertEqual(os.listdir(yedekler), ["feribot_yedek_2026-07-27.db"])
            yedek = sqlite3.connect(ilk)
            try:
                self.assertEqual(
                    yedek.execute("SELECT deger FROM kayitlar").fetchone()[0],
                    "korundu",
                )
                self.assertEqual(
                    yedek.execute("SELECT COUNT(*) FROM kayitlar").fetchone()[0],
                    2,
                )
            finally:
                yedek.close()

    def test_saklama_suresini_gecen_yedek_silinir(self):
        with tempfile.TemporaryDirectory() as klasor:
            kaynak = os.path.join(klasor, "kaynak.db")
            yedekler = os.path.join(klasor, "yedekler")
            os.makedirs(yedekler)
            eski = os.path.join(yedekler, "feribot_yedek_2026-06-01.db")
            with open(eski, "wb") as dosya:
                dosya.write(b"eski")
            baglanti = sqlite3.connect(kaynak)
            baglanti.execute("CREATE TABLE kayitlar(id INTEGER)")
            baglanti.commit()

            OtomatikYedek.olustur(
                kaynak,
                yedekler,
                baglanti=baglanti,
                simdi=datetime(2026, 7, 27),
                saklama_gunu=30,
            )
            baglanti.close()

            self.assertFalse(os.path.exists(eski))

    def test_yedek_dogrulanip_guvenli_geri_yuklenir(self):
        with tempfile.TemporaryDirectory() as klasor:
            kaynak = os.path.join(klasor, "kaynak.db")
            hedef = os.path.join(klasor, "hedef.db")
            yedekler = os.path.join(klasor, "yedekler")
            baglanti = sqlite3.connect(kaynak)
            baglanti.execute("CREATE TABLE gecisler(deger TEXT)")
            baglanti.execute("INSERT INTO gecisler VALUES ('yedek')")
            baglanti.commit()
            yedek = OtomatikYedek.olustur(
                kaynak, yedekler, baglanti=baglanti
            )
            baglanti.close()
            mevcut = sqlite3.connect(hedef)
            mevcut.execute("CREATE TABLE gecisler(deger TEXT)")
            mevcut.execute("INSERT INTO gecisler VALUES ('eski')")
            mevcut.commit()
            mevcut.close()

            sonuc, guvenlik = OtomatikYedek.geri_yukle(yedek, hedef)

            self.assertEqual(sonuc, hedef)
            self.assertTrue(os.path.exists(guvenlik))
            yuklenen = sqlite3.connect(hedef)
            try:
                self.assertEqual(
                    yuklenen.execute(
                        "SELECT deger FROM gecisler"
                    ).fetchone()[0],
                    "yedek",
                )
            finally:
                yuklenen.close()
