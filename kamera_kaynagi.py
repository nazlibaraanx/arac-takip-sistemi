import json
import os
import tempfile

from ayarlar import PROJE_KLASORU, VIDEO_YOLU


AYAR_DOSYASI = os.path.join(PROJE_KLASORU, "kamera_ayari.json")
KAYNAK_TURLERI = {"video", "usb"}


def varsayilan_ayar():
    return {"tur": "video", "deger": VIDEO_YOLU}


def kamera_ayarini_yukle(dosya_yolu=AYAR_DOSYASI):
    if not os.path.exists(dosya_yolu):
        return varsayilan_ayar()

    try:
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            ayar = json.load(dosya)
        return kamera_ayarini_dogrula(ayar)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return varsayilan_ayar()


def kamera_ayarini_dogrula(ayar):
    if not isinstance(ayar, dict):
        raise ValueError("Kamera ayarı geçersiz.")

    tur = str(ayar.get("tur", "")).strip().lower()
    deger = ayar.get("deger")
    if tur not in KAYNAK_TURLERI:
        raise ValueError("Kamera kaynak türü geçersiz.")

    if tur == "usb":
        try:
            deger = int(deger)
        except (TypeError, ValueError) as hata:
            raise ValueError("USB kamera numarası 0, 1 veya 2 olmalıdır.") from hata
        if deger < 0:
            raise ValueError("USB kamera numarası negatif olamaz.")
    else:
        deger = str(deger or "").strip()
        if not deger:
            raise ValueError("Kamera kaynağı boş bırakılamaz.")
    return {"tur": tur, "deger": deger}


def kamera_ayarini_kaydet(ayar, dosya_yolu=AYAR_DOSYASI):
    ayar = kamera_ayarini_dogrula(ayar)
    hedef_klasor = os.path.dirname(os.path.abspath(dosya_yolu))
    os.makedirs(hedef_klasor, exist_ok=True)

    tanimlayici, gecici_yol = tempfile.mkstemp(
        prefix=".kamera_",
        suffix=".json",
        dir=hedef_klasor,
    )
    try:
        with os.fdopen(tanimlayici, "w", encoding="utf-8") as dosya:
            json.dump(ayar, dosya, ensure_ascii=False, indent=2)
        os.replace(gecici_yol, dosya_yolu)
    finally:
        if os.path.exists(gecici_yol):
            os.remove(gecici_yol)
    return ayar


def video_kaynagini_getir(dosya_yolu=AYAR_DOSYASI):
    ayar = kamera_ayarini_yukle(dosya_yolu)
    return ayar["deger"]


def kamera_kaynagi_aciklamasi(ayar):
    ayar = kamera_ayarini_dogrula(ayar)
    adlar = {
        "video": "Kayıtlı Video",
        "usb": "USB Kamera",
    }
    return f"{adlar[ayar['tur']]} · {ayar['deger']}"
