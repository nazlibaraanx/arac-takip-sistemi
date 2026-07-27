import csv
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


EGITIM_KLASORU = Path(__file__).resolve().parent
VERI_SETI = EGITIM_KLASORU / "veri_seti"
GORUNTULER = VERI_SETI / "ham_kareler"
ETIKETLER = VERI_SETI / "on_etiketler"
CIKTI = EGITIM_KLASORU / "ciktilar" / "etiket_inceleme"

SINIFLAR = [
    "Motosiklet",
    "Çapa",
    "Otomobil",
    "Toplu Taşıma",
    "Traktör Römorklu",
    "Kamyonet",
    "Kamyon",
    "Uzun Araç",
]

RENKLER = [
    "#8E44AD",
    "#16A085",
    "#2F75B5",
    "#27AE60",
    "#D4AC0D",
    "#E67E22",
    "#C0392B",
    "#34495E",
]


def font_yukle(boyut, kalin=False):
    ad = "arialbd.ttf" if kalin else "arial.ttf"
    yollar = [Path("C:/Windows/Fonts") / ad, Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for yol in yollar:
        if yol.exists():
            return ImageFont.truetype(str(yol), boyut)
    return ImageFont.load_default()


BASLIK_FONTU = font_yukle(23, kalin=True)
ETIKET_FONTU = font_yukle(17, kalin=True)
KUCUK_FONT = font_yukle(15)


def etiketleri_oku(goruntu_yolu):
    goreli = goruntu_yolu.relative_to(GORUNTULER).with_suffix(".txt")
    etiket_yolu = ETIKETLER / goreli
    kutular = []
    if not etiket_yolu.exists():
        return kutular

    with Image.open(goruntu_yolu) as goruntu:
        genislik, yukseklik = goruntu.size

    for satir_no, satir in enumerate(etiket_yolu.read_text(encoding="utf-8").splitlines(), 1):
        if not satir.strip():
            continue
        sinif_id, merkez_x, merkez_y, kutu_genisligi, kutu_yuksekligi = map(float, satir.split())
        x1 = (merkez_x - kutu_genisligi / 2) * genislik
        y1 = (merkez_y - kutu_yuksekligi / 2) * yukseklik
        x2 = (merkez_x + kutu_genisligi / 2) * genislik
        y2 = (merkez_y + kutu_yuksekligi / 2) * yukseklik
        kutular.append(
            {
                "satir_no": satir_no,
                "sinif_id": int(sinif_id),
                "xyxy": (x1, y1, x2, y2),
                "yolo": satir,
            }
        )
    return kutular


def cerceveli_kare(goruntu_yolu, kare_no):
    goruntu = Image.open(goruntu_yolu).convert("RGB")
    cizim = ImageDraw.Draw(goruntu)
    kutular = etiketleri_oku(goruntu_yolu)
    for kutu in kutular:
        x1, y1, x2, y2 = kutu["xyxy"]
        sinif_id = kutu["sinif_id"]
        renk = RENKLER[sinif_id]
        cizim.rectangle((x1, y1, x2, y2), outline=renk, width=3)
        yazi = f"K{kare_no:02d}-{kutu['satir_no']:02d} {SINIFLAR[sinif_id]}"
        metin_kutusu = cizim.textbbox((x1, y1), yazi, font=ETIKET_FONTU)
        metin_yuksekligi = metin_kutusu[3] - metin_kutusu[1] + 6
        etiket_y = max(0, y1 - metin_yuksekligi)
        cizim.rectangle(
            (x1, etiket_y, min(goruntu.width, x1 + metin_kutusu[2] - metin_kutusu[0] + 8), y1),
            fill=renk,
        )
        cizim.text((x1 + 4, etiket_y + 2), yazi, fill="white", font=ETIKET_FONTU)
    return goruntu, kutular


def tam_kare_sayfalari(goruntuler, tum_kutular):
    klasor = CIKTI / "tam_kareler"
    klasor.mkdir(parents=True, exist_ok=True)
    hucre_genisligi = 960
    hucre_yuksekligi = 620
    for sayfa_no, baslangic in enumerate(range(0, len(goruntuler), 4), 1):
        sayfa = Image.new("RGB", (hucre_genisligi * 2, hucre_yuksekligi * 2), "#E2E8F0")
        cizim = ImageDraw.Draw(sayfa)
        for yerel_indeks, goruntu_yolu in enumerate(goruntuler[baslangic : baslangic + 4]):
            kare_no = baslangic + yerel_indeks + 1
            sutun = yerel_indeks % 2
            satir = yerel_indeks // 2
            x = sutun * hucre_genisligi
            y = satir * hucre_yuksekligi
            cerceveli, kutular = cerceveli_kare(goruntu_yolu, kare_no)
            cerceveli.thumbnail((940, 564), Image.Resampling.LANCZOS)
            sayfa.paste(cerceveli, (x + 10, y + 44))
            cizim.text(
                (x + 10, y + 10),
                f"K{kare_no:02d} | {goruntu_yolu.name} | {len(kutular)} kutu",
                fill="#0F172A",
                font=BASLIK_FONTU,
            )
            tum_kutular.extend((kare_no, goruntu_yolu, kutu) for kutu in kutular)
        sayfa.save(klasor / f"tam_kare_{sayfa_no:02d}.png", quality=95)


def kutu_sayfalari(tum_kutular, klasor_adi="arac_kutulari", dosya_on_eki="arac_kutulari"):
    klasor = CIKTI / klasor_adi
    klasor.mkdir(parents=True, exist_ok=True)
    hucre_genisligi = 360
    hucre_yuksekligi = 250
    sutun_sayisi = 4
    satir_sayisi = 4
    sayfa_kapasitesi = sutun_sayisi * satir_sayisi

    acik_goruntu_yolu = None
    acik_goruntu = None
    for sayfa_no, baslangic in enumerate(range(0, len(tum_kutular), sayfa_kapasitesi), 1):
        sayfa = Image.new(
            "RGB",
            (hucre_genisligi * sutun_sayisi, hucre_yuksekligi * satir_sayisi),
            "#E2E8F0",
        )
        cizim = ImageDraw.Draw(sayfa)
        for yerel_indeks, (kare_no, goruntu_yolu, kutu) in enumerate(
            tum_kutular[baslangic : baslangic + sayfa_kapasitesi]
        ):
            if goruntu_yolu != acik_goruntu_yolu:
                if acik_goruntu is not None:
                    acik_goruntu.close()
                acik_goruntu = Image.open(goruntu_yolu).convert("RGB")
                acik_goruntu_yolu = goruntu_yolu

            x1, y1, x2, y2 = kutu["xyxy"]
            genislik = max(1, x2 - x1)
            yukseklik = max(1, y2 - y1)
            pay = max(8, min(45, int(max(genislik, yukseklik) * 0.25)))
            kirpma = acik_goruntu.crop(
                (
                    max(0, int(x1) - pay),
                    max(0, int(y1) - pay),
                    min(acik_goruntu.width, int(x2) + pay),
                    min(acik_goruntu.height, int(y2) + pay),
                )
            )
            kirpma.thumbnail((340, 190), Image.Resampling.LANCZOS)
            sutun = yerel_indeks % sutun_sayisi
            satir = yerel_indeks // sutun_sayisi
            x = sutun * hucre_genisligi
            y = satir * hucre_yuksekligi
            sayfa.paste(kirpma, (x + (hucre_genisligi - kirpma.width) // 2, y + 48))
            sinif_id = kutu["sinif_id"]
            cizim.rectangle((x, y, x + hucre_genisligi - 1, y + 42), fill=RENKLER[sinif_id])
            cizim.text(
                (x + 8, y + 8),
                f"K{kare_no:02d}-{kutu['satir_no']:02d} | {SINIFLAR[sinif_id]}",
                fill="white",
                font=ETIKET_FONTU,
            )
        sayfa.save(klasor / f"{dosya_on_eki}_{sayfa_no:02d}.png", quality=95)

    if acik_goruntu is not None:
        acik_goruntu.close()


def indeks_yaz(tum_kutular):
    with (CIKTI / "inceleme_indeksi.csv").open("w", encoding="utf-8-sig", newline="") as dosya:
        yazici = csv.writer(dosya)
        yazici.writerow(["kare_no", "kutu_no", "goruntu", "sinif_id", "sinif", "yolo"])
        for kare_no, goruntu_yolu, kutu in tum_kutular:
            yazici.writerow(
                [
                    kare_no,
                    kutu["satir_no"],
                    goruntu_yolu.relative_to(GORUNTULER).as_posix(),
                    kutu["sinif_id"],
                    SINIFLAR[kutu["sinif_id"]],
                    kutu["yolo"],
                ]
            )


def main():
    if CIKTI.exists():
        shutil.rmtree(CIKTI)
    CIKTI.mkdir(parents=True)
    goruntuler = sorted(GORUNTULER.rglob("*.jpg"))
    tum_kutular = []
    tam_kare_sayfalari(goruntuler, tum_kutular)
    kutu_sayfalari(tum_kutular)
    supheli_kutular = []
    for kayit in tum_kutular:
        kutu = kayit[2]
        x1, y1, x2, y2 = kutu["xyxy"]
        alan_orani = ((x2 - x1) * (y2 - y1)) / (960 * 576)
        if kutu["sinif_id"] != 2 or alan_orani >= 0.015:
            supheli_kutular.append(kayit)
    kutu_sayfalari(
        supheli_kutular,
        klasor_adi="supheli_kutular",
        dosya_on_eki="supheli_kutular",
    )
    indeks_yaz(tum_kutular)
    print(f"{len(goruntuler)} kare ve {len(tum_kutular)} kutu için inceleme sayfaları hazırlandı.")
    print(CIKTI)


if __name__ == "__main__":
    main()
