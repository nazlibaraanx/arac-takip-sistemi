import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


PROJE_KLASORU = Path(__file__).resolve().parent.parent
VARSAYILAN_KAYNAK = PROJE_KLASORU / "videolar" / "egitim_ham"
VARSAYILAN_HEDEF = Path(__file__).resolve().parent / "veri_seti" / "ham_kareler"


def zaman_noktalarini_olustur(sure, aralik, maksimum):
    if sure <= 0:
        return []

    adet = int(sure // aralik) + 1
    if maksimum and adet > maksimum:
        return np.linspace(0, max(0, sure - 0.1), maksimum).tolist()
    return [sira * aralik for sira in range(adet)]


def goruntu_ozelliklerini_hesapla(kare):
    yukseklik, genislik = kare.shape[:2]
    roi = kare[
        int(yukseklik * 0.32):int(yukseklik * 0.95),
        int(genislik * 0.25):int(genislik * 0.95)
    ]
    gri = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    netlik = float(cv2.Laplacian(gri, cv2.CV_64F).var())
    kucuk = cv2.resize(gri, (160, 96), interpolation=cv2.INTER_AREA)
    return netlik, kucuk


def videodan_kareleri_cikar(
    video_yolu,
    hedef_klasor,
    aralik,
    maksimum,
    netlik_esigi,
    degisim_esigi
):
    kamera = cv2.VideoCapture(str(video_yolu))
    if not kamera.isOpened():
        print(f"Video açılamadı: {video_yolu}")
        return []

    fps = float(kamera.get(cv2.CAP_PROP_FPS) or 0)
    kare_sayisi = int(kamera.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sure = kare_sayisi / fps if fps > 0 else 0
    zamanlar = zaman_noktalarini_olustur(sure, aralik, maksimum)
    video_hedefi = hedef_klasor / video_yolu.stem
    video_hedefi.mkdir(parents=True, exist_ok=True)

    onceki_kucuk = None
    kayitlar = []

    for zaman in zamanlar:
        kamera.set(cv2.CAP_PROP_POS_MSEC, zaman * 1000)
        basarili, kare = kamera.read()
        if not basarili:
            continue

        netlik, kucuk = goruntu_ozelliklerini_hesapla(kare)
        degisim = (
            100.0
            if onceki_kucuk is None
            else float(cv2.absdiff(kucuk, onceki_kucuk).mean())
        )

        if netlik < netlik_esigi or degisim < degisim_esigi:
            continue

        saniye = int(round(zaman))
        dosya_adi = f"{video_yolu.stem}_{saniye:06d}s.jpg"
        cikti_yolu = video_hedefi / dosya_adi
        kodlandi, veri = cv2.imencode(
            ".jpg",
            kare,
            [cv2.IMWRITE_JPEG_QUALITY, 92]
        )
        if not kodlandi:
            print(f"Kare kodlanamadı: {cikti_yolu}")
            continue

        # NumPy tofile, OpenCV imwrite'ın Türkçe karakter içeren Windows
        # yollarında yaşadığı dosya yazma sorununu önler.
        veri.tofile(str(cikti_yolu))
        if not cikti_yolu.exists():
            print(f"Kare kaydedilemedi: {cikti_yolu}")
            continue
        onceki_kucuk = kucuk
        kayitlar.append(
            {
                "video": video_yolu.name,
                "zaman_saniye": f"{zaman:.2f}",
                "kare": int(round(zaman * fps)),
                "netlik": f"{netlik:.2f}",
                "degisim": f"{degisim:.2f}",
                "dosya": str(cikti_yolu.relative_to(hedef_klasor.parent))
            }
        )

    kamera.release()
    print(
        f"{video_yolu.name}: {len(kayitlar)} kare seçildi "
        f"({sure / 60:.1f} dakika)."
    )
    return kayitlar


def manifestoyu_yaz(hedef_klasor, kayitlar):
    manifesto_yolu = hedef_klasor.parent / "kare_manifestosu.csv"
    with manifesto_yolu.open("w", newline="", encoding="utf-8-sig") as dosya:
        alanlar = [
            "video",
            "zaman_saniye",
            "kare",
            "netlik",
            "degisim",
            "dosya"
        ]
        yazici = csv.DictWriter(dosya, fieldnames=alanlar)
        yazici.writeheader()
        yazici.writerows(kayitlar)
    return manifesto_yolu


def argumanlari_al():
    parser = argparse.ArgumentParser(
        description="Kamera videolarından eğitim için dengeli ve net kareler çıkarır."
    )
    parser.add_argument("--kaynak", type=Path, default=VARSAYILAN_KAYNAK)
    parser.add_argument("--hedef", type=Path, default=VARSAYILAN_HEDEF)
    parser.add_argument("--aralik", type=float, default=5.0)
    parser.add_argument("--maksimum-video-basina", type=int, default=0)
    parser.add_argument("--netlik-esigi", type=float, default=35.0)
    parser.add_argument("--degisim-esigi", type=float, default=1.5)
    return parser.parse_args()


def main():
    args = argumanlari_al()
    args.hedef.mkdir(parents=True, exist_ok=True)
    videolar = sorted(args.kaynak.glob("*.mp4"))
    if not videolar:
        raise SystemExit(f"MP4 video bulunamadı: {args.kaynak}")

    tum_kayitlar = []
    for video_yolu in videolar:
        tum_kayitlar.extend(
            videodan_kareleri_cikar(
                video_yolu=video_yolu,
                hedef_klasor=args.hedef,
                aralik=max(args.aralik, 0.5),
                maksimum=max(args.maksimum_video_basina, 0),
                netlik_esigi=max(args.netlik_esigi, 0),
                degisim_esigi=max(args.degisim_esigi, 0)
            )
        )

    manifesto_yolu = manifestoyu_yaz(args.hedef, tum_kayitlar)
    print(f"Toplam {len(tum_kayitlar)} kare hazırlandı.")
    print(f"Manifesto: {manifesto_yolu}")


if __name__ == "__main__":
    main()
