import re

import numpy as np


class TekilNesneHafizasi:
    """Bir yükleme boyunca sayılan nesnelerin anonim görünüm özetini tutar."""

    def __init__(self, hash_esigi=5, histogram_esigi=0.96):
        self.hash_esigi = int(hash_esigi)
        self.histogram_esigi = float(histogram_esigi)
        self.sifirla()

    def sifirla(self):
        self.gorunumler = {"arac": [], "yaya": []}
        self.plakalar = set()

    @staticmethod
    def plakayi_normalize_et(plaka):
        deger = re.sub(r"[^A-Z0-9]", "", str(plaka or "").upper())
        if not deger or deger == "OKUNAMADI":
            return ""
        return deger

    def plakalari_yukle(self, plakalar):
        for plaka in plakalar or []:
            normal = self.plakayi_normalize_et(plaka)
            if normal:
                self.plakalar.add(normal)

    @staticmethod
    def _kirp(kare, kutu):
        if kare is None or kutu is None or len(kutu) < 4:
            return None
        yukseklik, genislik = kare.shape[:2]
        x1, y1, x2, y2 = map(int, kutu[:4])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(genislik, x2), min(yukseklik, y2)
        if x2 <= x1 or y2 <= y1:
            return None
        return kare[y1:y2, x1:x2]

    @classmethod
    def gorunum_ozeti_olustur(cls, kare, kutu):
        kirpim = cls._kirp(kare, kutu)
        if kirpim is None or kirpim.size == 0:
            return None

        gri = (
            kirpim[:, :, 0].astype(np.float32) * 0.114
            + kirpim[:, :, 1].astype(np.float32) * 0.587
            + kirpim[:, :, 2].astype(np.float32) * 0.299
        )
        y_indeksleri = np.linspace(0, gri.shape[0] - 1, 8).astype(int)
        x_indeksleri = np.linspace(0, gri.shape[1] - 1, 9).astype(int)
        gri = gri[np.ix_(y_indeksleri, x_indeksleri)]
        farklar = gri[:, 1:] > gri[:, :-1]
        gorunum_hash = np.packbits(farklar.astype(np.uint8)).tobytes()

        renk_kodlari = (
            (kirpim[:, :, 0].astype(np.int32) // 64) * 16
            + (kirpim[:, :, 1].astype(np.int32) // 64) * 4
            + (kirpim[:, :, 2].astype(np.int32) // 64)
        )
        histogram = np.bincount(
            renk_kodlari.ravel(), minlength=64
        ).astype(np.float32)
        norm = np.linalg.norm(histogram)
        if norm > 0:
            histogram /= norm
        return gorunum_hash, histogram

    @staticmethod
    def _hash_uzakligi(sol, sag):
        return sum(
            int((a ^ b).bit_count())
            for a, b in zip(sol, sag)
        )

    def daha_once_sayildi_mi(
        self, nesne_turu, kare, kutu, etiket="", plaka=""
    ):
        normal_plaka = self.plakayi_normalize_et(plaka)
        if normal_plaka and normal_plaka in self.plakalar:
            return True

        ozet = self.gorunum_ozeti_olustur(kare, kutu)
        if ozet is None:
            return False
        gorunum_hash, histogram = ozet
        for kayit in self.gorunumler.get(nesne_turu, []):
            if etiket and kayit["etiket"] and etiket != kayit["etiket"]:
                continue
            hash_uzakligi = self._hash_uzakligi(
                gorunum_hash, kayit["hash"]
            )
            histogram_benzerligi = float(
                np.dot(histogram, kayit["histogram"])
            )
            if (
                hash_uzakligi <= self.hash_esigi
                and histogram_benzerligi >= self.histogram_esigi
            ):
                return True
        return False

    def kaydet(self, nesne_turu, kare, kutu, etiket="", plaka=""):
        normal_plaka = self.plakayi_normalize_et(plaka)
        if normal_plaka:
            self.plakalar.add(normal_plaka)
        ozet = self.gorunum_ozeti_olustur(kare, kutu)
        if ozet is None:
            return
        gorunum_hash, histogram = ozet
        self.gorunumler.setdefault(nesne_turu, []).append({
            "hash": gorunum_hash,
            "histogram": histogram,
            "etiket": str(etiket or ""),
        })
