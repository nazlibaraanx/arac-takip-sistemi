import os
import shutil
import time


class SistemSagligi:
    """Kamera akışı ve disk alanı için düşük maliyetli saha kontrolleri."""

    def __init__(
        self,
        proje_klasoru,
        donma_suresi=5.0,
        minimum_disk_gb=2.0,
        zaman_fonksiyonu=time.monotonic,
    ):
        self.proje_klasoru = proje_klasoru
        self.donma_suresi = float(donma_suresi)
        self.minimum_disk_bayt = int(float(minimum_disk_gb) * 1024 ** 3)
        self.zaman = zaman_fonksiyonu
        self.son_imza = None
        self.son_degisim = self.zaman()

    @staticmethod
    def _kare_imzasi(kare):
        if kare is None or getattr(kare, "size", 0) == 0:
            return None
        yukseklik, genislik = kare.shape[:2]
        ornek = kare[::max(1, yukseklik // 12), ::max(1, genislik // 12)]
        return (
            round(float(ornek.mean()), 2),
            round(float(ornek.std()), 2),
        )

    def kareyi_kontrol_et(self, kare):
        simdi = self.zaman()
        imza = self._kare_imzasi(kare)
        if imza is None:
            return "Kamera görüntüsü alınamıyor."
        if imza != self.son_imza:
            self.son_imza = imza
            self.son_degisim = simdi
            return None
        if simdi - self.son_degisim >= self.donma_suresi:
            return f"Kamera görüntüsü {self.donma_suresi:g} saniyedir donmuş."
        return None

    def diski_kontrol_et(self):
        bos_bayt = shutil.disk_usage(self.proje_klasoru).free
        if bos_bayt < self.minimum_disk_bayt:
            return (
                "Disk alanı kritik seviyede: "
                f"{bos_bayt / 1024 ** 3:.1f} GB boş."
            )
        return None
