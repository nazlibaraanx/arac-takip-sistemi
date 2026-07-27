import os
import tempfile
import unittest

from kamera_kaynagi import (
    kamera_ayarini_kaydet,
    kamera_ayarini_yukle,
    video_kaynagini_getir,
)


class KameraKaynagiTestleri(unittest.TestCase):

    def test_usb_kamera_numarasi_tamsayi_olarak_kaydedilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "kamera.json")
            kamera_ayarini_kaydet({"tur": "usb", "deger": "1"}, yol)
            self.assertEqual(kamera_ayarini_yukle(yol), {
                "tur": "usb",
                "deger": 1,
            })
            self.assertEqual(video_kaynagini_getir(yol), 1)

    def test_gecersiz_usb_numarasi_reddedilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "kamera.json")
            with self.assertRaises(ValueError):
                kamera_ayarini_kaydet({"tur": "usb", "deger": "kamera"}, yol)

    def test_ip_kamera_turu_reddedilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = os.path.join(klasor, "kamera.json")
            with self.assertRaises(ValueError):
                kamera_ayarini_kaydet({
                    "tur": "ip",
                    "deger": "rtsp://192.168.1.20/stream",
                }, yol)


if __name__ == "__main__":
    unittest.main()
