import time

import cv2


class VideoKontrolleri:
    """OpenCV video penceresine tıklanabilir kontrol butonları ekler."""

    BUTON_GENISLIGI = 210
    BUTON_YUKSEKLIGI = 42
    KENAR_BOSLUGU = 18
    BUTON_ARALIGI = 10

    def __init__(self):
        self.butonlar = {}
        self.bekleyen_eylem = None
        self.durum_mesaji = ""
        self.durum_rengi = (255, 255, 255)
        self.durum_bitis_zamani = 0.0

    def fare_olayi(self, olay, x, y, bayraklar, parametre):
        if olay != cv2.EVENT_LBUTTONUP:
            return

        for eylem, (x1, y1, x2, y2) in self.butonlar.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.bekleyen_eylem = eylem
                return

    def eylemi_al(self):
        eylem = self.bekleyen_eylem
        self.bekleyen_eylem = None
        return eylem

    def mesaj_goster(self, mesaj, basarili=True, sure=4.0):
        self.durum_mesaji = mesaj
        self.durum_rengi = (80, 220, 80) if basarili else (60, 60, 255)
        self.durum_bitis_zamani = time.monotonic() + sure

    def _buton_ciz(self, kare, alan, etiket, renk):
        x1, y1, x2, y2 = alan

        cv2.rectangle(kare, (x1, y1), (x2, y2), renk, -1)
        cv2.rectangle(kare, (x1, y1), (x2, y2), (255, 255, 255), 2)

        metin_boyutu, _ = cv2.getTextSize(
            etiket,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            2
        )
        metin_x = x1 + (self.BUTON_GENISLIGI - metin_boyutu[0]) // 2
        metin_y = y1 + (self.BUTON_YUKSEKLIGI + metin_boyutu[1]) // 2

        cv2.putText(
            kare,
            etiket,
            (metin_x, metin_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    def ciz(self, kare):
        yukseklik, genislik = kare.shape[:2]
        x2 = genislik - self.KENAR_BOSLUGU
        x1 = max(self.KENAR_BOSLUGU, x2 - self.BUTON_GENISLIGI)
        ilk_y1 = self.KENAR_BOSLUGU
        ilk_y2 = ilk_y1 + self.BUTON_YUKSEKLIGI
        self.butonlar = {
            "kayitlari_ac": (x1, ilk_y1, x2, ilk_y2)
        }

        self._buton_ciz(
            kare,
            self.butonlar["kayitlari_ac"],
            "Kayitlari Ac",
            (180, 90, 20)
        )

        if self.durum_mesaji and time.monotonic() < self.durum_bitis_zamani:
            metin_y = max(30, yukseklik - 25)
            cv2.putText(
                kare,
                self.durum_mesaji,
                (self.KENAR_BOSLUGU, metin_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                self.durum_rengi,
                2,
                cv2.LINE_AA
            )
        elif self.durum_mesaji:
            self.durum_mesaji = ""

        return kare
