import random
import shutil
from pathlib import Path


EGITIM_KLASORU = Path(__file__).resolve().parent
VERI_SETI = EGITIM_KLASORU / "veri_seti"
GORUNTULER = VERI_SETI / "ham_kareler"
ONAYLI_ETIKETLER = VERI_SETI / "onayli_etiketler"


def main():
    etiketler = sorted(ONAYLI_ETIKETLER.rglob("*.txt"))
    if len(etiketler) < 10:
        raise SystemExit(
            "Eğitim/doğrulama ayrımı için en az 10 onaylanmış kare gerekiyor."
        )

    eslesmeler = []
    for etiket_yolu in etiketler:
        goreli = etiket_yolu.relative_to(ONAYLI_ETIKETLER)
        goruntu_yolu = (GORUNTULER / goreli).with_suffix(".jpg")
        if goruntu_yolu.exists():
            eslesmeler.append((goruntu_yolu, etiket_yolu))

    rastgele = random.Random(42)
    rastgele.shuffle(eslesmeler)
    dogrulama_adedi = max(1, round(len(eslesmeler) * 0.20))
    dogrulama = eslesmeler[:dogrulama_adedi]
    egitim = eslesmeler[dogrulama_adedi:]

    for grup_adi, grup in (("train", egitim), ("val", dogrulama)):
        goruntu_hedefi = VERI_SETI / "images" / grup_adi
        etiket_hedefi = VERI_SETI / "labels" / grup_adi
        goruntu_hedefi.mkdir(parents=True, exist_ok=True)
        etiket_hedefi.mkdir(parents=True, exist_ok=True)

        for goruntu_yolu, etiket_yolu in grup:
            # Video adı dosya adına eklendiği için kare adları benzersizdir.
            shutil.copy2(goruntu_yolu, goruntu_hedefi / goruntu_yolu.name)
            shutil.copy2(etiket_yolu, etiket_hedefi / etiket_yolu.name)

    print(f"Eğitim: {len(egitim)} kare")
    print(f"Doğrulama: {len(dogrulama)} kare")


if __name__ == "__main__":
    main()
