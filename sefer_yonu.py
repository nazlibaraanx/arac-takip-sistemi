import json
import os
import tempfile

from ayarlar import PROJE_KLASORU


MALATYA_BASKIL = "Malatya - Baskil"
BASKIL_MALATYA = "Baskil - Malatya"
SEFER_YONLERI = (MALATYA_BASKIL, BASKIL_MALATYA)
AYAR_DOSYASI = os.path.join(PROJE_KLASORU, "sefer_yonu.json")


def sefer_yonunu_dogrula(sefer_yonu):
    sefer_yonu = str(sefer_yonu or "").strip()
    if sefer_yonu not in SEFER_YONLERI:
        raise ValueError("Geçerli bir sefer yönü seçin.")
    return sefer_yonu


def sefer_yonunu_oku(dosya_yolu=AYAR_DOSYASI):
    if not os.path.exists(dosya_yolu):
        return MALATYA_BASKIL
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            return sefer_yonunu_dogrula(json.load(dosya).get("sefer_yonu"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return MALATYA_BASKIL


def sefer_yonunu_yaz(sefer_yonu, dosya_yolu=AYAR_DOSYASI):
    sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
    klasor = os.path.dirname(os.path.abspath(dosya_yolu))
    os.makedirs(klasor, exist_ok=True)
    tanimlayici, gecici_yol = tempfile.mkstemp(
        prefix=".sefer_", suffix=".json", dir=klasor
    )
    try:
        with os.fdopen(tanimlayici, "w", encoding="utf-8") as dosya:
            json.dump(
                {"sefer_yonu": sefer_yonu},
                dosya,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(gecici_yol, dosya_yolu)
    finally:
        if os.path.exists(gecici_yol):
            os.remove(gecici_yol)
    return sefer_yonu


def dosya_etiketi(sefer_yonu):
    return sefer_yonunu_dogrula(sefer_yonu).replace(" - ", "_")


def ters_sefer_yonu(sefer_yonu):
    sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
    if sefer_yonu == MALATYA_BASKIL:
        return BASKIL_MALATYA
    return MALATYA_BASKIL
