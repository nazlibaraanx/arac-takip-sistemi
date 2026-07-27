import json
import os
import tempfile

from ayarlar import PROJE_KLASORU


DURUM_DOSYASI = os.path.join(PROJE_KLASORU, "yukleme_durumu.json")


def yukleme_bilgisini_oku(dosya_yolu=DURUM_DOSYASI, varsayilan=False):
    if not os.path.exists(dosya_yolu):
        return {"aktif": bool(varsayilan), "sefer_id": None}
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)
        sefer_id = veri.get("sefer_id")
        return {
            "aktif": bool(veri.get("aktif", varsayilan)),
            "sefer_id": int(sefer_id) if sefer_id is not None else None,
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {"aktif": bool(varsayilan), "sefer_id": None}


def yukleme_durumunu_oku(dosya_yolu=DURUM_DOSYASI, varsayilan=False):
    return yukleme_bilgisini_oku(dosya_yolu, varsayilan)["aktif"]


def yukleme_durumunu_yaz(
    aktif, dosya_yolu=DURUM_DOSYASI, sefer_id=None
):
    hedef_klasor = os.path.dirname(os.path.abspath(dosya_yolu))
    os.makedirs(hedef_klasor, exist_ok=True)
    tanimlayici, gecici_yol = tempfile.mkstemp(
        prefix=".yukleme_",
        suffix=".json",
        dir=hedef_klasor,
    )
    try:
        with os.fdopen(tanimlayici, "w", encoding="utf-8") as dosya:
            json.dump(
                {
                    "aktif": bool(aktif),
                    "sefer_id": int(sefer_id) if sefer_id is not None else None,
                },
                dosya,
                indent=2,
            )
        os.replace(gecici_yol, dosya_yolu)
    finally:
        if os.path.exists(gecici_yol):
            os.remove(gecici_yol)
    return bool(aktif)
