import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import cv2

from ayarlar import GECIS_SAG_X_ORANI, GECIS_SOL_X_ORANI


class GecisKontrol:
    """Araçların feribot kapağından tek yönde ve yalnızca bir kez geçmesini izler."""

    DURUM_GIRIS_BEKLIYOR = "GIRIS_BEKLIYOR"
    DURUM_BITIS_BEKLIYOR = "BITIS_BEKLIYOR"
    DURUM_TAMAMLANDI = "TAMAMLANDI"

    def __init__(self) -> None:
        # Çizgilerin görüntü yüksekliğine göre konumları.
        self.giris_y_orani = 0.54
        self.bitis_y_orani = 0.70

        # Geçerli geçiş alanının yatay sınırları.
        self.sol_x_orani = GECIS_SOL_X_ORANI
        self.sag_x_orani = GECIS_SAG_X_ORANI

        # Hareket ve takip ayarları.
        self.minimum_hareket_piksel = 2
        self.kayip_arac_silme_suresi = 30.0
        self.tamamlanan_arac_silme_suresi = 5.0

        # Her araç için durum bilgisi.
        self.arac_durumlari: Dict[int, Dict[str, Any]] = {}

        # Tamamlanan ID'ler video oturumu boyunca tutulur. Plaka okunamasa bile
        # aynı takip ID'sine sahip araç ikinci kez sayılmaz.
        self.tamamlanan_araclar: Set[int] = set()

        self.toplam_gecen_arac = 0

        # Kare gönderilmeden çizgi çizilmesi ihtimaline karşı varsayılan boyut.
        self.son_genislik = 1024
        self.son_yukseklik = 576

    def noktalari_hesapla(
        self,
        kare=None,
    ) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
        if kare is not None:
            self.son_yukseklik, self.son_genislik = kare.shape[:2]

        sol_x = int(self.son_genislik * self.sol_x_orani)
        sag_x = int(self.son_genislik * self.sag_x_orani)
        giris_y = int(self.son_yukseklik * self.giris_y_orani)
        bitis_y = int(self.son_yukseklik * self.bitis_y_orani)

        return (
            (sol_x, giris_y),
            (sag_x, giris_y),
            (sol_x, bitis_y),
            (sag_x, bitis_y),
        )

    def cizgileri_ciz(self, kare):
        giris_baslangic, giris_bitis, bitis_baslangic, bitis_bitis = (
            self.noktalari_hesapla(kare)
        )

        # Geçiş bölgesini hafifçe renklendir.
        katman = kare.copy()
        cv2.rectangle(
            katman,
            giris_baslangic,
            bitis_bitis,
            (0, 180, 255),
            -1,
        )
        cv2.addWeighted(katman, 0.10, kare, 0.90, 0, kare)

        cv2.line(kare, giris_baslangic, giris_bitis, (255, 0, 0), 3)
        cv2.putText(
            kare,
            "Kapak Girisi",
            (giris_baslangic[0], max(25, giris_baslangic[1] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 0, 0),
            2,
        )

        cv2.line(kare, bitis_baslangic, bitis_bitis, (0, 255, 0), 3)
        cv2.putText(
            kare,
            "Kapak Bitisi",
            (bitis_baslangic[0], max(25, bitis_baslangic[1] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
        )

        return kare

    @staticmethod
    def arac_bilgilerini_al(arac: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(arac, dict):
            return None

        arac_id = arac.get("id", arac.get("takip_id", arac.get("track_id")))

        x1 = arac.get("x1")
        y1 = arac.get("y1")
        x2 = arac.get("x2")
        y2 = arac.get("y2")

        if None in (x1, y1, x2, y2):
            kutu = arac.get("kutu", arac.get("bbox"))
            if kutu is not None and len(kutu) >= 4:
                x1, y1, x2, y2 = kutu[:4]

        if arac_id is None or None in (x1, y1, x2, y2):
            return None

        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        if x2 <= x1 or y2 <= y1:
            return None

        return {
            "id": int(arac_id),
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "sinif": arac.get(
                "sinif",
                arac.get("arac_turu", arac.get("class_name", "Bilinmiyor")),
            ),
        }

    @staticmethod
    def cizgi_asagi_gecildi(onceki_y: int, simdiki_y: int, cizgi_y: int) -> bool:
        """Noktanın çizgiyi yukarıdan aşağıya geçtiğini kontrol eder."""
        return onceki_y < cizgi_y <= simdiki_y

    def yatay_alanda_mi(self, merkez_x: int) -> bool:
        sol_x = int(self.son_genislik * self.sol_x_orani)
        sag_x = int(self.son_genislik * self.sag_x_orani)
        return sol_x <= merkez_x <= sag_x

    def yeni_durum_olustur(
        self,
        alt_orta_x: int,
        alt_orta_y: int,
        sinif: str,
        simdi: float,
    ) -> Dict[str, Any]:
        return {
            "durum": self.DURUM_GIRIS_BEKLIYOR,
            "onceki_x": alt_orta_x,
            "onceki_y": alt_orta_y,
            "son_gorulme": simdi,
            "ilk_gorulme": simdi,
            "sinif": sinif,
            "sayildi": False,
        }

    def eski_araclari_temizle(self, simdi: Optional[float] = None) -> None:
        simdi = time.time() if simdi is None else simdi
        silinecek_idler: List[int] = []

        for arac_id, durum in self.arac_durumlari.items():
            gecen_sure = simdi - durum["son_gorulme"]
            zaman_asimi = (
                self.tamamlanan_arac_silme_suresi
                if durum["durum"] == self.DURUM_TAMAMLANDI
                else self.kayip_arac_silme_suresi
            )

            if gecen_sure > zaman_asimi:
                silinecek_idler.append(arac_id)

        for arac_id in silinecek_idler:
            self.arac_durumlari.pop(arac_id, None)
            # Hareket geçmişi bellekten temizlenir; tamamlanan ID ise oturum
            # bitene kadar korunur. Böylece aynı araç tekrar sayılmaz.

    def araclari_kontrol_et(
        self,
        araclar: Iterable[Dict[str, Any]],
        kare=None,
    ) -> List[Dict[str, Any]]:
        tamamlananlar: List[Dict[str, Any]] = []
        simdi = time.time()

        _, giris_bitis, _, bitis_bitis = self.noktalari_hesapla(kare)
        giris_y = giris_bitis[1]
        bitis_y = bitis_bitis[1]

        for arac in araclar or []:
            bilgiler = self.arac_bilgilerini_al(arac)
            if bilgiler is None:
                continue

            arac_id = bilgiler["id"]
            alt_orta_x = (bilgiler["x1"] + bilgiler["x2"]) // 2
            alt_orta_y = bilgiler["y2"]
            sinif = bilgiler["sinif"]

            if arac_id not in self.arac_durumlari:
                self.arac_durumlari[arac_id] = self.yeni_durum_olustur(
                    alt_orta_x,
                    alt_orta_y,
                    sinif,
                    simdi,
                )
                print(f"Yeni araç bulundu -> ID {arac_id}")
                continue

            durum = self.arac_durumlari[arac_id]
            onceki_y = durum["onceki_y"]
            y_hareketi = alt_orta_y - onceki_y

            durum["son_gorulme"] = simdi
            durum["sinif"] = sinif

            # Çok küçük titreşimleri gerçek hareket sayma.
            yeterli_hareket = y_hareketi >= self.minimum_hareket_piksel
            yatay_alanda = self.yatay_alanda_mi(alt_orta_x)

            if (
                durum["durum"] == self.DURUM_GIRIS_BEKLIYOR
                and yatay_alanda
                and yeterli_hareket
                and self.cizgi_asagi_gecildi(onceki_y, alt_orta_y, giris_y)
            ):
                durum["durum"] = self.DURUM_BITIS_BEKLIYOR
                print(f"ID {arac_id} -> KAPAK GİRİŞİNİ GEÇTİ")

            elif (
                durum["durum"] == self.DURUM_BITIS_BEKLIYOR
                and yatay_alanda
                and yeterli_hareket
                and self.cizgi_asagi_gecildi(onceki_y, alt_orta_y, bitis_y)
            ):
                durum["durum"] = self.DURUM_TAMAMLANDI

                if not durum["sayildi"] and arac_id not in self.tamamlanan_araclar:
                    durum["sayildi"] = True
                    self.tamamlanan_araclar.add(arac_id)
                    self.toplam_gecen_arac += 1

                    tamamlananlar.append(
                        {
                            "id": arac_id,
                            "sinif": sinif,
                            "nokta": (alt_orta_x, alt_orta_y),
                        }
                    )

                    print(f"ID {arac_id} -> FERİBOTA TAMAMEN GİRDİ")
                    print(f"Toplam geçen araç: {self.toplam_gecen_arac}")

            durum["onceki_x"] = alt_orta_x
            durum["onceki_y"] = alt_orta_y

        # Araç listesi boş olsa da eski kayıtların temizlenmesini sağlar.
        self.eski_araclari_temizle(simdi)
        return tamamlananlar
