import sys
import types
import unittest
import numpy as np


try:
    import cv2
except ImportError:
    cv2 = sys.modules.get("cv2", types.SimpleNamespace())

if not hasattr(cv2, "EVENT_LBUTTONUP"):
    cv2.EVENT_LBUTTONUP = 4
    cv2.FONT_HERSHEY_SIMPLEX = 0
    cv2.LINE_AA = 16
    cv2.rectangle = lambda *args, **kwargs: None
    cv2.putText = lambda *args, **kwargs: None
    cv2.getTextSize = lambda metin, *args: ((len(metin) * 10, 16), 0)
    sys.modules["cv2"] = cv2

from video_kontrolleri import VideoKontrolleri


class VideoKontrolleriTestleri(unittest.TestCase):

    def setUp(self):
        self.kontroller = VideoKontrolleri()
        self.kontroller.ciz(np.zeros((720, 1280, 3), dtype=np.uint8))

    def buton_merkezi(self, eylem):
        x1, y1, x2, y2 = self.kontroller.butonlar[eylem]
        return (x1 + x2) // 2, (y1 + y2) // 2

    def test_kayit_butonu_dogru_eylemi_uretir(self):
        x, y = self.buton_merkezi("kayitlari_ac")

        self.kontroller.fare_olayi(4, x, y, None, None)

        self.assertEqual(self.kontroller.eylemi_al(), "kayitlari_ac")
        self.assertIsNone(self.kontroller.eylemi_al())

    def test_video_ekraninda_yalnizca_kayit_butonu_vardir(self):
        self.assertEqual(
            set(self.kontroller.butonlar),
            {"kayitlari_ac"}
        )

    def test_buton_disindaki_tiklama_eylem_uretmez(self):
        self.kontroller.fare_olayi(4, 5, 5, None, None)

        self.assertIsNone(self.kontroller.eylemi_al())


if __name__ == "__main__":
    unittest.main()
