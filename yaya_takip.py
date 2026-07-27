from ayarlar import GECIS_SAG_X_ORANI, GECIS_SOL_X_ORANI


class YayaTakip:
    """Yayaları geçiş alanında, giriş yönünde ve yalnızca bir kez sayar."""

    def __init__(
        self,
        min_gorulme=3,
        giris_y_orani=0.54,
        bitis_y_orani=0.70,
        sol_x_orani=GECIS_SOL_X_ORANI,
        sag_x_orani=GECIS_SAG_X_ORANI,
    ):
        self.min_gorulme = max(1, int(min_gorulme))
        self.giris_y_orani = float(giris_y_orani)
        self.bitis_y_orani = float(bitis_y_orani)
        self.sol_x_orani = float(sol_x_orani)
        self.sag_x_orani = float(sag_x_orani)
        self.gorulme_sayilari = {}
        self.durumlar = {}
        self.sayilan_idler = set()
        self.toplam_yaya = 0

    @staticmethod
    def _kutu_al(nesne):
        kutu = nesne.get("kutu", nesne.get("bbox"))
        if kutu is None or len(kutu) < 4:
            return None
        x1, y1, x2, y2 = map(int, kutu[:4])
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2

    def guncelle(self, nesneler, kare=None):
        yeni_yayalar = []
        if kare is None or len(kare.shape) < 2:
            return yeni_yayalar

        yukseklik, genislik = kare.shape[:2]
        giris_y = int(yukseklik * self.giris_y_orani)
        bitis_y = int(yukseklik * self.bitis_y_orani)
        sol_x = int(genislik * self.sol_x_orani)
        sag_x = int(genislik * self.sag_x_orani)

        for nesne in nesneler or []:
            if nesne.get("sinif") != "Yaya Yolcu":
                continue

            takip_id = nesne.get("id")
            if takip_id is None or takip_id in self.sayilan_idler:
                continue
            kutu = self._kutu_al(nesne)
            if kutu is None:
                continue

            x1, _, x2, y2 = kutu
            merkez_x = (x1 + x2) // 2
            yatay_alanda = sol_x <= merkez_x <= sag_x

            gorulme = self.gorulme_sayilari.get(takip_id, 0) + 1
            self.gorulme_sayilari[takip_id] = gorulme
            durum = self.durumlar.get(takip_id)
            if durum is None:
                self.durumlar[takip_id] = {"onceki_y": y2, "giris_gecti": False}
                continue

            onceki_y = durum["onceki_y"]
            asagi_hareket = y2 > onceki_y
            if (
                yatay_alanda
                and asagi_hareket
                and onceki_y < giris_y <= y2
            ):
                durum["giris_gecti"] = True

            if (
                gorulme >= self.min_gorulme
                and durum["giris_gecti"]
                and yatay_alanda
                and asagi_hareket
                and onceki_y < bitis_y <= y2
            ):
                self.sayilan_idler.add(takip_id)
                self.toplam_yaya += 1
                yeni_yayalar.append(nesne)

            durum["onceki_y"] = y2
        return yeni_yayalar
