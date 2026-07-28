import csv


def dogruluk_raporu_hesapla(satirlar):
    """Sistem ve görevli sayımlarını mutlak hata üzerinden karşılaştırır."""

    sonuc = {}
    for alan in ("arac", "yaya"):
        gercek_toplam = sum(int(s[f"gorevli_{alan}"]) for s in satirlar)
        sistem_toplam = sum(int(s[f"sistem_{alan}"]) for s in satirlar)
        mutlak_hata = sum(
            abs(int(s[f"sistem_{alan}"]) - int(s[f"gorevli_{alan}"]))
            for s in satirlar
        )
        hata_orani = mutlak_hata / max(1, gercek_toplam)
        sonuc[alan] = {
            "gorevli_toplami": gercek_toplam,
            "sistem_toplami": sistem_toplam,
            "mutlak_hata": mutlak_hata,
            "dogruluk_yuzdesi": max(0.0, (1.0 - hata_orani) * 100),
        }
    return sonuc


def saha_csv_oku(dosya_yolu):
    with open(dosya_yolu, "r", encoding="utf-8-sig", newline="") as dosya:
        return list(csv.DictReader(dosya))


def saha_sablonu_olustur(dosya_yolu):
    alanlar = (
        "tarih", "sefer_yonu", "sefer_no",
        "gorevli_arac", "sistem_arac", "gorevli_yaya", "sistem_yaya",
    )
    with open(dosya_yolu, "w", encoding="utf-8-sig", newline="") as dosya:
        csv.DictWriter(dosya, fieldnames=alanlar).writeheader()
    return dosya_yolu
