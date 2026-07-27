from pathlib import Path

from ultralytics import YOLO


PROJE_KLASORU = Path(__file__).resolve().parent.parent
EGITIM_KLASORU = Path(__file__).resolve().parent
VERI_YAML = EGITIM_KLASORU / "veri.yaml"
BASLANGIC_MODELI = PROJE_KLASORU / "modeller" / "yolov8m.pt"


def main():
    etiketler = list((EGITIM_KLASORU / "veri_seti" / "labels").rglob("*.txt"))
    if not etiketler:
        raise SystemExit(
            "Henüz YOLO etiketi bulunmuyor. Kareler etiketlenmeden eğitim başlatılamaz."
        )

    model = YOLO(str(BASLANGIC_MODELI))
    model.train(
        data=str(VERI_YAML),
        epochs=80,
        imgsz=640,
        batch=8,
        patience=15,
        project=str(EGITIM_KLASORU / "ciktilar"),
        name="feribot_arac_modeli",
        exist_ok=True
    )


if __name__ == "__main__":
    main()
