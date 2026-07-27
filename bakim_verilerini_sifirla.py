from excel_aktar import ExcelAktar
from veritabani import Veritabani
from sefer_yonu import SEFER_YONLERI


def main():
    veritabani = Veritabani()
    try:
        veritabani.tum_rapor_verilerini_sil()
        rapor_yolu = ExcelAktar.rapor_merkezini_guncelle({
            sefer_yonu: veritabani.gunluk_ozetleri_getir(sefer_yonu)
            for sefer_yonu in SEFER_YONLERI
        }, sefer_ozetleri=veritabani.sefer_ozetlerini_getir())
        print("Veritabani, grafik ve aylik rapor verileri sifirlandi.")
        print("Bos rapor merkezi:", rapor_yolu)
    finally:
        veritabani.baglantiyi_kapat()


if __name__ == "__main__":
    main()
