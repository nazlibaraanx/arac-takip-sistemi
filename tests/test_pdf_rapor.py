import os
import tempfile
import unittest
from datetime import datetime

from pdf_rapor import PdfRapor


class PdfRaporTestleri(unittest.TestCase):

    def test_tarih_araligi_grafigi_pdf_olusturulur(self):
        with tempfile.TemporaryDirectory() as klasor:
            dosya_yolu = os.path.join(klasor, "tarih_araligi.pdf")
            sonuc = PdfRapor.tarih_araligi_olustur(
                dosya_yolu=dosya_yolu,
                baslangic=datetime(2026, 7, 22),
                bitis=datetime(2026, 7, 24),
                gunluk_ozetler=[
                    ("22.07.2026", 6, 2, 1520.0),
                    ("23.07.2026", 0, 0, 0.0),
                    ("24.07.2026", 4, 3, 960.0)
                ],
                grafik_modu="arac"
            )
            self.assertEqual(sonuc, dosya_yolu)
            self.assertTrue(os.path.exists(dosya_yolu))
            self.assertGreater(os.path.getsize(dosya_yolu), 4000)
            with open(dosya_yolu, "rb") as pdf_dosyasi:
                self.assertEqual(pdf_dosyasi.read(5), b"%PDF-")

    def test_grafikli_aylik_pdf_olusturulur(self):
        with tempfile.TemporaryDirectory() as klasor:
            dosya_yolu = os.path.join(klasor, "aylik_rapor.pdf")

            sonuc = PdfRapor.olustur(
                dosya_yolu=dosya_yolu,
                yil=2026,
                ay=7,
                gunluk_ozetler=[
                    ("21.07.2026", 17, 8, 4860.0),
                    ("22.07.2026", 22, 11, 7240.0),
                    ("23.07.2026", 19, 9, 6180.0)
                ],
                arac_turleri=[
                    ("Otomobil", 31),
                    ("Toplu Taşıma", 16),
                    ("Kamyon", 11)
                ]
            )

            self.assertEqual(sonuc, dosya_yolu)
            self.assertTrue(os.path.exists(dosya_yolu))
            self.assertGreater(os.path.getsize(dosya_yolu), 5000)
            with open(dosya_yolu, "rb") as pdf_dosyasi:
                self.assertEqual(pdf_dosyasi.read(5), b"%PDF-")

    def test_yaya_aylik_pdf_olusturulur(self):
        with tempfile.TemporaryDirectory() as klasor:
            dosya_yolu = os.path.join(klasor, "yaya_aylik_rapor.pdf")
            PdfRapor.olustur(
                dosya_yolu=dosya_yolu,
                yil=2026,
                ay=7,
                gunluk_ozetler=[("22.07.2026", 16, 9, 3960.0)],
                arac_turleri=[("Otomobil", 13), ("Toplu Taşıma", 3)],
                grafik_modu="yaya",
            )
            self.assertTrue(os.path.exists(dosya_yolu))
            self.assertGreater(os.path.getsize(dosya_yolu), 4000)


if __name__ == "__main__":
    unittest.main()
