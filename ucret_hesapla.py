from veritabani import Veritabani


class UcretHesapla:

    def __init__(self, veritabani=None):
        self.veritabani = veritabani or Veritabani()
        self._baglantinin_sahibi = veritabani is None

        # YOLO sınıflarını veritabanındaki araç isimlerine çevir
        self.sinif_haritasi = {
            "car": "Otomobil",
            "truck": "Kamyon",
            "bus": "Toplu Taşıma",
            "motorcycle": "Motosiklet",
            "Otobüs": "Toplu Taşıma",
            "Servis": "Toplu Taşıma",
            "Minibüs": "Toplu Taşıma"
        }

    def ucret_hesapla(self, arac_turu, uzunluk_metre=None):

        # İngilizce geldiyse Türkçeye çevir
        arac_turu = self.sinif_haritasi.get(arac_turu, arac_turu)

        ucret = self.veritabani.ucret_getir(
            arac_turu,
            uzunluk_metre=uzunluk_metre
        )

        if ucret == 0:
            print(f"Uyarı: '{arac_turu}' için ücret bulunamadı.")
            return 0

        return ucret

    def baglantiyi_kapat(self):
        if self._baglantinin_sahibi:
            self.veritabani.baglantiyi_kapat()
