"""90 karelik gorsel taramada bulunan on etiket hatalarini kalici kaydeder."""

import csv
from pathlib import Path


EGITIM_KLASORU = Path(__file__).resolve().parent
INDEKS = EGITIM_KLASORU / "ciktilar" / "etiket_inceleme" / "inceleme_indeksi.csv"
DUZELTMELER = EGITIM_KLASORU / "veri_seti" / "on_etiket_duzeltmeleri.csv"
SILMELER = EGITIM_KLASORU / "veri_seti" / "on_etiket_silmeleri.csv"
ALANLAR = ["goruntu", "sinif_id", "merkez_x", "merkez_y", "genislik", "yukseklik"]


# Kodu inceleme sayfalarindaki Kxx-yy numaralariyla tutmak, yapilan her
# degisikligin hangi kutudan geldigini tekrar kontrol edilebilir kilar.
TOPLU_TASIMA = {
    "K02-02", "K03-02", "K04-01", "K05-04", "K06-04", "K07-01",
    "K07-03", "K07-04", "K08-04", "K08-05", "K09-01", "K09-03",
    "K15-02", "K16-01", "K25-04", "K25-08", "K26-04", "K28-02",
    "K28-05", "K29-01", "K29-03", "K30-05", "K30-09", "K31-06",
    "K32-03", "K33-01", "K33-03", "K33-05", "K34-01", "K34-04",
    "K34-10", "K35-01", "K35-02", "K36-03", "K45-01", "K54-01",
    "K54-04", "K55-02", "K55-05", "K56-04", "K57-03", "K57-06",
    "K58-02", "K58-06", "K59-02", "K59-05", "K60-04", "K60-05",
    "K61-04", "K61-05", "K62-02", "K62-06", "K63-03", "K63-04",
    "K70-01", "K71-01", "K72-01", "K73-02", "K74-02", "K75-01",
    "K76-02", "K78-01", "K85-03", "K86-03", "K87-03", "K88-02",
    "K89-02", "K90-05",
}

KAMYONET = {
    "K07-06", "K08-01", "K29-07", "K30-03", "K32-07", "K32-08",
    "K34-03", "K34-13", "K54-02", "K54-05", "K55-11", "K58-08",
    "K59-06", "K59-09", "K60-06", "K61-06", "K76-01", "K85-02",
    "K85-08", "K87-05", "K88-05",
}

OTOMOBIL = {"K42-01", "K60-13", "K61-13"}

# K87-04 ve K87-07 ayni mavi cekiciye ait iki kutudur. Genis olan manuel
# kutu iki otomatik kutuyu da bastirarak tek Kamyon etiketi birakir.
KAMYON = {"K87-07", "K89-05"}

# Insan ve genis/kismi yinelenen arac kutulari cikartilir.
SILINECEK = {"K13-01", "K60-14", "K61-14"}


# Modelin tumden kacirdigi gorunur araclar. Degerler YOLO xywhn bicimindedir.
EK_KUTULAR = [
    ("A01_20260714_060710/A01_20260714_060710_002321s.jpg", 3, 0.773438, 0.747396, 0.453125, 0.505208),
    ("A01_20260714_060710/A01_20260714_060710_002611s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_060710/A01_20260714_060710_002901s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_060710/A01_20260714_060710_003192s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_060710/A01_20260714_060710_003482s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_060710/A01_20260714_060710_003772s.jpg", 3, 0.770833, 0.763021, 0.458333, 0.473958),
    ("A01_20260714_060710/A01_20260714_060710_004062s.jpg", 5, 0.617188, 0.886285, 0.432292, 0.227431),
    ("A01_20260714_062806/A01_20260714_062806_000987s.jpg", 3, 0.830729, 0.776042, 0.338542, 0.447917),
    ("A01_20260714_062806/A01_20260714_062806_001481s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_062806/A01_20260714_062806_001728s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_062806/A01_20260714_062806_001975s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_062806/A01_20260714_062806_002221s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_062806/A01_20260714_062806_002468s.jpg", 3, 0.783854, 0.760417, 0.432292, 0.479167),
    ("A01_20260714_062806/A01_20260714_062806_002715s.jpg", 5, 0.611979, 0.894097, 0.348958, 0.211806),
    ("A01_20260714_082725/A01_20260714_082725_003798s.jpg", 3, 0.875000, 0.303819, 0.171875, 0.111111),
]


def kod(satir):
    return f"K{int(satir['kare_no']):02d}-{int(satir['kutu_no']):02d}"


def yolo_degerleri(satir):
    parcalar = satir["yolo"].split()
    return [float(deger) for deger in parcalar[1:]]


def kayit(goruntu, sinif_id, degerler):
    return {
        "goruntu": goruntu.replace("\\", "/"),
        "sinif_id": str(sinif_id),
        "merkez_x": f"{degerler[0]:.6f}",
        "merkez_y": f"{degerler[1]:.6f}",
        "genislik": f"{degerler[2]:.6f}",
        "yukseklik": f"{degerler[3]:.6f}",
    }


def anahtar(satir):
    return tuple(satir[alan] for alan in ALANLAR if alan != "sinif_id")


def main():
    with INDEKS.open("r", encoding="utf-8-sig", newline="") as dosya:
        indeks = list(csv.DictReader(dosya))

    bulunan = {kod(satir): satir for satir in indeks}
    sinif_gruplari = ((TOPLU_TASIMA, 3), (KAMYONET, 5), (OTOMOBIL, 2), (KAMYON, 6))
    gerekli = set().union(*(grup for grup, _ in sinif_gruplari), SILINECEK)
    eksik = sorted(gerekli - bulunan.keys())
    if eksik:
        raise SystemExit("Inceleme indeksinde bulunamayan kutular: " + ", ".join(eksik))

    mevcut = []
    if DUZELTMELER.exists():
        with DUZELTMELER.open("r", encoding="utf-8-sig", newline="") as dosya:
            mevcut = list(csv.DictReader(dosya))

    yeni = mevcut[:]
    for grup, sinif_id in sinif_gruplari:
        for kutu_kodu in sorted(grup):
            satir = bulunan[kutu_kodu]
            yeni.append(kayit(satir["goruntu"], sinif_id, yolo_degerleri(satir)))

    for goruntu, sinif_id, *degerler in EK_KUTULAR:
        yeni.append(kayit(goruntu, sinif_id, degerler))

    # Ayni koordinattaki son karar gecerlidir; boylece onceki manuel duzeltmeler
    # korunurken bu taramanin sinif kararlari uygulanir.
    tekil = {}
    for satir in yeni:
        tekil[anahtar(satir)] = satir

    DUZELTMELER.parent.mkdir(parents=True, exist_ok=True)
    with DUZELTMELER.open("w", encoding="utf-8-sig", newline="") as dosya:
        yazici = csv.DictWriter(dosya, fieldnames=ALANLAR)
        yazici.writeheader()
        yazici.writerows(tekil.values())

    silme_satirlari = []
    for kutu_kodu in sorted(SILINECEK):
        satir = bulunan[kutu_kodu]
        degerler = yolo_degerleri(satir)
        silme_satirlari.append(kayit(satir["goruntu"], 0, degerler))

    silme_alanlari = [alan for alan in ALANLAR if alan != "sinif_id"]
    with SILMELER.open("w", encoding="utf-8-sig", newline="") as dosya:
        yazici = csv.DictWriter(dosya, fieldnames=silme_alanlari)
        yazici.writeheader()
        for satir in silme_satirlari:
            yazici.writerow({alan: satir[alan] for alan in silme_alanlari})

    print(f"{len(tekil)} kalici duzeltme kutusu yazildi.")
    print(f"{len(silme_satirlari)} hatali kutu silme listesine yazildi.")


if __name__ == "__main__":
    main()
