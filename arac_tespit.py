from collections import defaultdict

from ultralytics import YOLO
from arac_siniflandirma import (
    SinifKararHafizasi,
    genis_toplu_tasima_govdesi_mi,
    kararli_sinifi_guncelle,
    otomobil_boyutunda_mi,
    toplu_tasima_duzeltmesi_gerekli_mi,
)
from ayarlar import (
    ARAC_SINIFLARI,
    GORUNTU_BOYUTU,
    GUVEN_ESIGI,
    MODEL_YOLU,
    OTOMOBIL_BOYUT_DUZELTME_AKTIF,
    OTOMOBIL_MAKS_BOY_EN_ORANI,
    OTOMOBIL_MAKS_GENISLIK_ORANI,
    OTOMOBIL_MIN_ALT_Y_ORANI,
    OTOMOBIL_MIN_GENISLIK_ORANI,
    SERVIS_DUZELTME_AKTIF,
    SERVIS_OTOMOBIL_DUZELTME_AKTIF,
    SERVIS_MAKS_GENISLIK_ORANI,
    SERVIS_MIN_ALT_Y_ORANI,
    SERVIS_MIN_BOY_EN_ORANI,
    SERVIS_OTOMOBIL_MAKS_GENISLIK_ORANI,
    TOPLU_TASIMA_GENIS_GOVDE_AKTIF,
    TOPLU_TASIMA_GENIS_GOVDE_MAKS_BOY_EN_ORANI,
    TOPLU_TASIMA_GENIS_GOVDE_MIN_ALT_Y_ORANI,
    TOPLU_TASIMA_GENIS_GOVDE_MIN_GENISLIK_ORANI,
)


class AracTespit:

    def __init__(self, sinif_duzeltmeleri=None):

        print("YOLO modeli yükleniyor...")

        self.model = YOLO(MODEL_YOLU)
        self.sinif_oylari = defaultdict(lambda: defaultdict(float))
        self.sinif_karar_hafizasi = SinifKararHafizasi()
        self.sinif_duzeltmeleri = dict(sinif_duzeltmeleri or {})

        # YOLO sınıflarını Türkçeye çevir
        self.sinif_haritasi = {
            "car": "Otomobil",
            "truck": "Kamyon",
            "bus": "Toplu Taşıma",
            "motorcycle": "Motosiklet",
            "person": "Yaya Yolcu",
            "bicycle": "Bisiklet",
            "train": "Tren"
        }

        print("Model başarıyla yüklendi.")

    def kararli_sinifi_guncelle(self, takip_id, sinif, guven):
        """Karelik sınıf sıçramalarını takip boyunca çoğunluk kararıyla süzer."""
        return kararli_sinifi_guncelle(
            self.sinif_oylari,
            takip_id,
            sinif,
            guven,
        )

    def oturumu_sifirla(self):
        """Yeni yükleme için takip ve sınıflandırma geçmişini temizler."""

        self.sinif_oylari.clear()
        self.sinif_karar_hafizasi.sifirla()
        predictor = getattr(self.model, "predictor", None)
        for tracker in getattr(predictor, "trackers", []) or []:
            reset = getattr(tracker, "reset", None)
            if callable(reset):
                reset()

    def araclari_bul(self, kare):

        sonuc = self.model.track(
            kare,
            persist=True,
            conf=GUVEN_ESIGI,
            imgsz=GORUNTU_BOYUTU,
            verbose=False
        )

        bulunan_araclar = []

        for r in sonuc:

            if r.boxes.id is None:
                continue

            for i in range(len(r.boxes)):

                # YOLO sınıfı
                takip_id = int(r.boxes.id[i])
                sinif_id = int(r.boxes.cls[i])
                model_sinifi = self.model.names[sinif_id]
                sinif = self.sinif_haritasi.get(model_sinifi, model_sinifi)
                model_turkce_sinifi = sinif
                guven = float(r.boxes.conf[i])

                x1, y1, x2, y2 = map(int, r.boxes.xyxy[i])
                kutu = (x1, y1, x2, y2)

                genis_toplu_tasima = (
                    TOPLU_TASIMA_GENIS_GOVDE_AKTIF
                    and model_sinifi in {"car", "truck", "bus"}
                    and genis_toplu_tasima_govdesi_mi(
                        kutu,
                        kare.shape,
                        TOPLU_TASIMA_GENIS_GOVDE_MIN_ALT_Y_ORANI,
                        TOPLU_TASIMA_GENIS_GOVDE_MIN_GENISLIK_ORANI,
                        TOPLU_TASIMA_GENIS_GOVDE_MAKS_BOY_EN_ORANI,
                    )
                )
                otomobil_boyutu = (
                    OTOMOBIL_BOYUT_DUZELTME_AKTIF
                    and not genis_toplu_tasima
                    and model_sinifi in {"car", "truck", "bus"}
                    and otomobil_boyutunda_mi(
                        kutu,
                        kare.shape,
                        OTOMOBIL_MIN_ALT_Y_ORANI,
                        OTOMOBIL_MIN_GENISLIK_ORANI,
                        OTOMOBIL_MAKS_GENISLIK_ORANI,
                        OTOMOBIL_MAKS_BOY_EN_ORANI,
                    )
                )

                servis_adayi = (
                    SERVIS_DUZELTME_AKTIF
                    and not otomobil_boyutu
                    and (
                        model_sinifi != "car"
                        or SERVIS_OTOMOBIL_DUZELTME_AKTIF
                    )
                    and toplu_tasima_duzeltmesi_gerekli_mi(
                        model_sinifi,
                        kutu,
                        kare.shape,
                        SERVIS_MIN_ALT_Y_ORANI,
                        SERVIS_MAKS_GENISLIK_ORANI,
                        SERVIS_MIN_BOY_EN_ORANI,
                        SERVIS_OTOMOBIL_MAKS_GENISLIK_ORANI
                    )
                )

                if genis_toplu_tasima:
                    sinif = "Toplu Taşıma"
                elif otomobil_boyutu and guven < 0.65:
                    sinif = "Otomobil"
                elif servis_adayi:
                    sinif = "Toplu Taşıma"

                # Gorsel olarak dogrulanmis takip kimlikleri, modelin gecici
                # sinif tahminlerinden ve servis geometrisi kuralindan ustundur.
                if model_sinifi != "person":
                    sinif = self.sinif_duzeltmeleri.get(takip_id, sinif)

                # Araç ve yaya yolcu dışındaki nesneleri geç.
                if sinif not in ARAC_SINIFLARI and sinif != "Yaya Yolcu":
                    continue

                if sinif != "Yaya Yolcu":
                    elle_duzeltildi = takip_id in self.sinif_duzeltmeleri
                    if elle_duzeltildi:
                        karar_guveni = 1.0
                    else:
                        sinif, karar_guveni = self.sinif_karar_hafizasi.guncelle(
                            takip_id,
                            model_turkce_sinifi,
                            sinif,
                            guven,
                            geometrik_kanit=(sinif != model_turkce_sinifi),
                        )
                else:
                    karar_guveni = guven

                arac = {
                    "id": takip_id,
                    "sinif": sinif,
                    "guven": karar_guveni,
                    "model_guveni": guven,
                    "model_sinifi": model_turkce_sinifi,
                    "kutu": kutu
                }

                bulunan_araclar.append(arac)

        return bulunan_araclar
