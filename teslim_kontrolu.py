import os

import cv2
import easyocr  # noqa: F401
import numpy  # noqa: F401
import openpyxl  # noqa: F401
import reportlab  # noqa: F401
import ultralytics  # noqa: F401

from ayarlar import MODEL_YOLU, VIDEO_YOLU
from veritabani import Veritabani


def calistir():
    print("VIDEO", VIDEO_YOLU, os.path.isfile(VIDEO_YOLU))
    print("MODEL", MODEL_YOLU, os.path.isfile(MODEL_YOLU))

    kamera = cv2.VideoCapture(VIDEO_YOLU)
    print(
        "VIDEO_BILGISI",
        kamera.isOpened(),
        int(kamera.get(cv2.CAP_PROP_FRAME_COUNT)),
        kamera.get(cv2.CAP_PROP_FPS),
        int(kamera.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(kamera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    basarili, kare = kamera.read()
    print("ILK_KARE", basarili, None if kare is None else kare.shape)
    kamera.release()

    veritabani = Veritabani()
    print(
        "SAYILAR",
        len(veritabani.gecis_ozetlerini_getir()),
        len(veritabani.gunluk_ozetleri_getir()),
        veritabani.toplam_yaya_sayisi(),
        len(veritabani.ucretleri_getir()),
    )
    veritabani.imlec.execute(
        "SELECT sql FROM sqlite_master WHERE name='yaya_gecisleri'"
    )
    print("YAYA_SEMASI", veritabani.imlec.fetchone()[0])
    veritabani.baglantiyi_kapat()
    print("ORTAM_KONTROLU_OK")


if __name__ == "__main__":
    calistir()
