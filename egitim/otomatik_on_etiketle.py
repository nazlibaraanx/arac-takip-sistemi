import csv
import sys
from pathlib import Path

from ultralytics import YOLO


PROJE_KLASORU = Path(__file__).resolve().parent.parent
EGITIM_KLASORU = Path(__file__).resolve().parent
GORUNTU_KLASORU = EGITIM_KLASORU / "veri_seti" / "ham_kareler"
CIKTI_KLASORU = EGITIM_KLASORU / "veri_seti" / "on_etiketler"
DUZELTME_DOSYASI = EGITIM_KLASORU / "veri_seti" / "on_etiket_duzeltmeleri.csv"
SILME_DOSYASI = EGITIM_KLASORU / "veri_seti" / "on_etiket_silmeleri.csv"
MODEL_YOLU = PROJE_KLASORU / "modeller" / "yolov8m.pt"

if str(PROJE_KLASORU) not in sys.path:
    sys.path.insert(0, str(PROJE_KLASORU))

from arac_siniflandirma import toplu_tasima_duzeltmesi_gerekli_mi
from ayarlar import (
    SERVIS_DUZELTME_AKTIF,
    SERVIS_MAKS_GENISLIK_ORANI,
    SERVIS_MIN_ALT_Y_ORANI,
    SERVIS_MIN_BOY_EN_ORANI,
    SERVIS_OTOMOBIL_MAKS_GENISLIK_ORANI,
)

# COCO sınıfları -> feribot eğitim sınıf numaraları.
SINIF_ESLEMESI = {
    "motorcycle": 0,
    "car": 2,
    "bus": 3,
    "truck": 6
}


def kutu_iou(birinci, ikinci):
    def koselere_cevir(xywh):
        merkez_x, merkez_y, genislik, yukseklik = xywh
        return (
            merkez_x - genislik / 2,
            merkez_y - yukseklik / 2,
            merkez_x + genislik / 2,
            merkez_y + yukseklik / 2,
        )

    ax1, ay1, ax2, ay2 = koselere_cevir(birinci)
    bx1, by1, bx2, by2 = koselere_cevir(ikinci)
    kesisim = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(
        0.0, min(ay2, by2) - max(ay1, by1)
    )
    birinci_alan = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    ikinci_alan = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    birlesim = birinci_alan + ikinci_alan - kesisim
    return kesisim / birlesim if birlesim > 0 else 0.0


def kucuk_kutu_kapsama_orani(birinci, ikinci):
    def koselere_cevir(xywh):
        merkez_x, merkez_y, genislik, yukseklik = xywh
        return (
            merkez_x - genislik / 2,
            merkez_y - yukseklik / 2,
            merkez_x + genislik / 2,
            merkez_y + yukseklik / 2,
        )

    ax1, ay1, ax2, ay2 = koselere_cevir(birinci)
    bx1, by1, bx2, by2 = koselere_cevir(ikinci)
    kesisim = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(
        0.0, min(ay2, by2) - max(ay1, by1)
    )
    kucuk_alan = min(
        max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1),
        max(0.0, bx2 - bx1) * max(0.0, by2 - by1),
    )
    return kesisim / kucuk_alan if kucuk_alan > 0 else 0.0


def adaylari_birlestir(adaylar):
    """Aynı araca ait üst üste kutuları tek etikete indirir."""

    birlesmis = []
    for aday in sorted(
        adaylar,
        key=lambda deger: (deger.get("manuel", False), deger["guven"]),
        reverse=True,
    ):
        ayni_kutu = next(
            (
                mevcut
                for mevcut in birlesmis
                if (
                    kutu_iou(mevcut["xywhn"], aday["xywhn"]) >= 0.85
                    or (
                        mevcut.get("manuel", False)
                        and kucuk_kutu_kapsama_orani(
                            mevcut["xywhn"], aday["xywhn"]
                        ) >= 0.55
                    )
                )
            ),
            None,
        )
        if ayni_kutu is None:
            birlesmis.append(aday.copy())
            continue

        # Manuel gorsel karar her zaman otomatik siniflandirmadan ustundur.
        # Yalnizca iki otomatik tahmin cakistiginda Toplu Tasima bilgisini koru.
        if (
            not ayni_kutu.get("manuel", False)
            and not aday.get("manuel", False)
            and aday["feribot_id"] == 3
        ):
            ayni_kutu["feribot_id"] = 3

    return birlesmis


def manuel_duzeltmeleri_oku():
    duzeltmeler = {}
    if not DUZELTME_DOSYASI.exists():
        return duzeltmeler

    with DUZELTME_DOSYASI.open("r", encoding="utf-8-sig", newline="") as dosya:
        for satir in csv.DictReader(dosya):
            goruntu = satir["goruntu"].replace("\\", "/")
            duzeltmeler.setdefault(goruntu, []).append(
                {
                    "feribot_id": int(satir["sinif_id"]),
                    "xywhn": tuple(
                        float(satir[alan])
                        for alan in ("merkez_x", "merkez_y", "genislik", "yukseklik")
                    ),
                    "guven": 2.0,
                    "manuel": True,
                }
            )
    return duzeltmeler


def manuel_silmeleri_oku():
    """Gorsel incelemede arac olmadigi kesinlesen kutulari okur."""

    silmeler = {}
    if not SILME_DOSYASI.exists():
        return silmeler

    with SILME_DOSYASI.open("r", encoding="utf-8-sig", newline="") as dosya:
        for satir in csv.DictReader(dosya):
            goruntu = satir["goruntu"].replace("\\", "/")
            silmeler.setdefault(goruntu, []).append(
                tuple(
                    float(satir[alan])
                    for alan in ("merkez_x", "merkez_y", "genislik", "yukseklik")
                )
            )
    return silmeler


def main():
    goruntuler = sorted(GORUNTU_KLASORU.rglob("*.jpg"))
    if not goruntuler:
        raise SystemExit(f"Ön etiketlenecek kare bulunamadı: {GORUNTU_KLASORU}")

    CIKTI_KLASORU.mkdir(parents=True, exist_ok=True)
    manuel_duzeltmeler = manuel_duzeltmeleri_oku()
    manuel_silmeler = manuel_silmeleri_oku()
    model = YOLO(str(MODEL_YOLU))

    toplam_kutu = 0
    duzeltilen_toplu_tasima = 0
    elenen_sahte_kamyon = 0
    birlestirilen_kutu = 0
    silinen_hatali_kutu = 0
    for sira, goruntu_yolu in enumerate(goruntuler, 1):
        # Tüm kareleri tek bir tensörde toplamak CPU belleğini aşabiliyor.
        # Model bellekte kalır; görüntüler ise güvenli biçimde tek tek işlenir.
        sonuc = model.predict(
            source=str(goruntu_yolu),
            conf=0.15,
            imgsz=960,
            device="cpu",
            agnostic_nms=True,
            max_det=100,
            verbose=False,
        )[0]
        adaylar = []
        if sonuc.boxes is not None:
            for kutu in sonuc.boxes:
                coco_id = int(kutu.cls[0])
                coco_adi = model.names[coco_id]
                feribot_id = SINIF_ESLEMESI.get(coco_adi)
                if feribot_id is None:
                    continue

                merkez_x, merkez_y, genislik, yukseklik = (
                    float(deger) for deger in kutu.xywhn[0]
                )

                # Feribotun sol yolcu bölümünü ve korkulukları kapsayan aşırı
                # büyük kutular bazı karelerde kamyon sanılıyor.
                if coco_adi == "truck" and genislik >= 0.35 and merkez_x < 0.45:
                    elenen_sahte_kamyon += 1
                    continue

                xyxy = tuple(float(deger) for deger in kutu.xyxy[0])
                if (
                    SERVIS_DUZELTME_AKTIF
                    and toplu_tasima_duzeltmesi_gerekli_mi(
                        coco_adi,
                        xyxy,
                        sonuc.orig_shape,
                        SERVIS_MIN_ALT_Y_ORANI,
                        SERVIS_MAKS_GENISLIK_ORANI,
                        SERVIS_MIN_BOY_EN_ORANI,
                        SERVIS_OTOMOBIL_MAKS_GENISLIK_ORANI,
                    )
                ):
                    feribot_id = 3
                    duzeltilen_toplu_tasima += 1

                adaylar.append(
                    {
                        "feribot_id": feribot_id,
                        "xywhn": (merkez_x, merkez_y, genislik, yukseklik),
                        "guven": float(kutu.conf[0]),
                        "manuel": False,
                    }
                )

        manuel_anahtar = goruntu_yolu.relative_to(GORUNTU_KLASORU).as_posix()
        silme_kutulari = manuel_silmeler.get(manuel_anahtar, [])
        if silme_kutulari:
            kalan_adaylar = []
            for aday in adaylar:
                silinsin = any(
                    kucuk_kutu_kapsama_orani(aday["xywhn"], silme_kutusu) >= 0.55
                    for silme_kutusu in silme_kutulari
                )
                if silinsin:
                    silinen_hatali_kutu += 1
                else:
                    kalan_adaylar.append(aday)
            adaylar = kalan_adaylar

        goreli = goruntu_yolu.relative_to(GORUNTU_KLASORU).with_suffix(".txt")
        adaylar.extend(manuel_duzeltmeler.get(manuel_anahtar, []))
        birlesmis_adaylar = adaylari_birlestir(adaylar)
        birlestirilen_kutu += len(adaylar) - len(birlesmis_adaylar)
        satirlar = []
        for aday in birlesmis_adaylar:
            merkez_x, merkez_y, genislik, yukseklik = aday["xywhn"]
            satirlar.append(
                f"{aday['feribot_id']} {merkez_x:.6f} {merkez_y:.6f} "
                f"{genislik:.6f} {yukseklik:.6f}"
            )

        etiket_yolu = CIKTI_KLASORU / goreli
        etiket_yolu.parent.mkdir(parents=True, exist_ok=True)
        icerik = "\n".join(satirlar)
        if icerik:
            icerik += "\n"
        etiket_yolu.write_text(icerik, encoding="utf-8")
        toplam_kutu += len(satirlar)
        if sira % 10 == 0 or sira == len(goruntuler):
            print(f"Yüksek çözünürlük taraması: {sira}/{len(goruntuler)}", flush=True)

    print(f"{len(goruntuler)} kare için {toplam_kutu} ön kutu hazırlandı.")
    print(
        f"{duzeltilen_toplu_tasima} servis/minibüs kutusu "
        "Toplu Taşıma olarak düzeltildi."
    )
    print(f"{elenen_sahte_kamyon} büyük yolcu-alanı kutusu elendi.")
    print(f"{birlestirilen_kutu} üst üste kutu birleştirildi.")
    print(f"{silinen_hatali_kutu} araç olmayan/yanlış kutu silindi.")
    print("Bu etiketler eğitimden önce etiketleme_araci.py ile onaylanmalıdır.")


if __name__ == "__main__":
    main()
