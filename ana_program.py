import os
import subprocess
import sys
import time
from datetime import date

import cv2

from ayarlar import PROJE_KLASORU
from arac_tespit import AracTespit
from excel_aktar import ExcelAktar
from gecis_kontrol import GecisKontrol
from kamera_kaynagi import kamera_ayarini_yukle, kamera_kaynagi_aciklamasi
from plaka_okuma import PlakaOkuma
from sefer_yonu import SEFER_YONLERI, sefer_yonunu_oku
from tek_ornek import TekOrnekKilidi
from ucret_hesapla import UcretHesapla
from veritabani import Veritabani
from video_kontrolleri import VideoKontrolleri
from yaya_takip import YayaTakip
from yukleme_durumu import yukleme_bilgisini_oku, yukleme_durumunu_yaz


# ==========================
# AYARLAR
# ==========================

KARE_ATLAMA = 3
PENCERE_ADI = "Akilli Feribot Gecis Sistemi"


# ==========================
# YARDIMCI FONKSİYONLAR
# ==========================

def arac_bul(araclar, arac_id):
    """
    Verilen ID'ye sahip aracı araç listesinden bulur.
    """

    for arac in araclar:
        if arac.get("id") == arac_id:
            return arac

    return None


def arac_kutusunu_ciz(kare, arac):
    """
    Araç kutusunu, bilgisini ve alt orta noktasını çizer.
    """

    kutu = arac.get("kutu")

    if kutu is None or len(kutu) != 4:
        return

    x1, y1, x2, y2 = map(int, kutu)

    arac_id = arac.get("id", "-")
    sinif = arac.get("sinif", "Bilinmiyor")
    guven = float(arac.get("guven", 0))

    genislik_px = max(0, x2 - x1)

    etiket = (
        f"ID:{arac_id} | "
        f"{sinif} | "
        f"{genislik_px}px | "
        f"%{guven * 100:.1f}"
    )

    renk = (0, 165, 255) if sinif == "Yaya Yolcu" else (0, 255, 0)

    cv2.rectangle(
        kare,
        (x1, y1),
        (x2, y2),
        renk,
        2
    )

    cv2.putText(
        kare,
        etiket,
        (x1, max(25, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        renk,
        2
    )

    merkez_x = int((x1 + x2) / 2)
    alt_y = int(y2)

    cv2.circle(
        kare,
        (merkez_x, alt_y),
        5,
        (0, 0, 255),
        -1
    )


def yonetim_panelini_ac(panel_sureci):
    """Yönetim panelini açar; zaten açıksa ikinci kopyayı başlatmaz."""

    if panel_sureci is not None and panel_sureci.poll() is None:
        return panel_sureci, False

    panel_yolu = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "yonetim_paneli.py"
    )
    panel_sureci = subprocess.Popen([sys.executable, panel_yolu])
    return panel_sureci, True


def video_penceresi_acik_mi():
    """OpenCV penceresinin kullanıcı tarafından kapatılıp kapatılmadığını denetler."""

    try:
        return cv2.getWindowProperty(
            PENCERE_ADI,
            cv2.WND_PROP_VISIBLE
        ) >= 1
    except cv2.error:
        return False


def otomatik_excel_raporunu_guncelle(veritabani):
    """Bütün kalıcı günlük toplamları tek filtreli Excel'de günceller."""

    dosya_yolu = ExcelAktar.rapor_merkezini_guncelle({
        sefer_yonu: veritabani.gunluk_ozetleri_getir(sefer_yonu)
        for sefer_yonu in SEFER_YONLERI
    }, sefer_ozetleri=veritabani.sefer_ozetlerini_getir())
    print("Excel rapor merkezi güncellendi:", dosya_yolu)
    return [dosya_yolu]


def gecisi_kaydet(
    veritabani,
    plaka_okuyucu,
    ucret_sistemi,
    kare,
    arac,
    sefer_yonu,
    sefer_id
):
    """
    Aracın plakasını okur, ücretini hesaplar
    ve veritabanına kaydeder.
    """

    try:
        kutu = arac.get("kutu")

        if kutu is None or len(kutu) != 4:
            print("Kayıt yapılamadı: Araç kutusu bulunamadı.")
            return None

        x1, y1, x2, y2 = map(int, kutu)

        takip_id = arac.get("id")
        arac_turu = arac.get("sinif", "Bilinmiyor")
        genislik_px = max(0, x2 - x1)

        sonuc = plaka_okuyucu.plaka_oku(
            kare,
            arac
        )

        if sonuc is None:
            sonuc = {}

        plaka_basarili = bool(sonuc.get("basarili", False))
        plaka = (
            sonuc.get("plaka", "OKUNAMADI")
            if plaka_basarili
            else "OKUNAMADI"
        )
        plaka_guveni = float(sonuc.get("guven", 0))

        ucret = ucret_sistemi.ucret_hesapla(
            arac_turu
        )

        # Parametreler isimle değil sırayla gönderiliyor.
        # Böylece eski keyword parametresi hatası engelleniyor.
        veritabani.gecis_kaydet(
            takip_id,
            plaka,
            arac_turu,
            genislik_px,
            ucret,
            sefer_yonu,
            sefer_id
        )

        print("=" * 50)
        print("ARAÇ FERİBOTA GİRDİ")
        print("ID      :", takip_id)
        print("SINIF   :", arac_turu)
        print("PLAKA   :", plaka)
        print("GÜVEN   :", round(plaka_guveni, 2))
        print("GENİŞLİK:", f"{genislik_px} px")
        print("ÜCRET   :", f"{ucret} TL")
        print("=" * 50)

        return float(ucret)

    except TypeError as hata:
        print("=" * 50)
        print("VERİTABANI PARAMETRE HATASI")
        print(hata)
        print("=" * 50)
        return None

    except Exception as hata:
        print("=" * 50)
        print("GEÇİŞ KAYDI SIRASINDA HATA OLUŞTU")
        print(type(hata).__name__, ":", hata)
        print("=" * 50)
        return None


def ana_program():
    """
    Feribot araç geçiş sisteminin ana çalışma fonksiyonu.
    """

    kamera = None
    veritabani = None
    panel_sureci = None
    uygulama_kilidi = TekOrnekKilidi(
        os.path.join(PROJE_KLASORU, ".ana_program.lock")
    )

    try:
        if not uygulama_kilidi.al():
            print(
                "Ana geçiş sistemi zaten çalışıyor. "
                "İkinci kopya başlatılmadı."
            )
            return

        # ==========================
        # NESNELER
        # ==========================

        print("Sistem başlatılıyor...")

        kamera_ayari = kamera_ayarini_yukle()
        video_kaynagi = kamera_ayari["deger"]
        veritabani = Veritabani()
        print("Geçmiş geçiş kayıtları korunarak yeni oturum başlatıldı.")
        try:
            otomatik_excel_raporunu_guncelle(veritabani)
        except Exception as hata:
            print("Başlangıç Excel güncelleme hatası:", hata)
        tespit = AracTespit()
        gecis_kontrol = GecisKontrol()
        yaya_takip = YayaTakip(min_gorulme=3)
        plaka_okuyucu = PlakaOkuma()
        ucret_sistemi = UcretHesapla(veritabani)
        video_kontrolleri = VideoKontrolleri()

        # ==========================
        # VİDEO
        # ==========================

        print("Görüntü kaynağı:", kamera_kaynagi_aciklamasi(kamera_ayari))
        kamera = cv2.VideoCapture(video_kaynagi)

        if not kamera.isOpened():
            raise RuntimeError(
                f"Görüntü kaynağı açılamadı: {video_kaynagi}"
            )

        cv2.namedWindow(PENCERE_ADI, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(
            PENCERE_ADI,
            video_kontrolleri.fare_olayi
        )

        # ==========================
        # DEĞİŞKENLER
        # ==========================

        kare_sayaci = 0
        son_araclar = []
        son_rapor_gunu = date.today()

        onceki_zaman = time.time()
        ortalama_fps = 0.0
        yukleme_bilgisi = yukleme_bilgisini_oku(
            varsayilan=False
        )
        yukleme_aktif = yukleme_bilgisi["aktif"]
        aktif_sefer_id = yukleme_bilgisi["sefer_id"]
        aktif_sefer_yonu = sefer_yonunu_oku()
        if yukleme_aktif and aktif_sefer_id is None:
            aktif_sefer_id = veritabani.sefer_baslat(aktif_sefer_yonu)
            yukleme_durumunu_yaz(True, sefer_id=aktif_sefer_id)

        print("Sistem hazır.")
        print("Çıkmak için Q tuşuna basın.")

        # ==========================
        # ANA DÖNGÜ
        # ==========================

        while True:

            basarili, kare = kamera.read()

            if not basarili:
                print("Video bitti.")
                break

            kare_sayaci += 1
            yeni_yukleme_bilgisi = {
                "aktif": yukleme_aktif,
                "sefer_id": aktif_sefer_id,
            }
            if kare_sayaci % 10 == 0:
                yeni_yukleme_bilgisi = yukleme_bilgisini_oku(
                    varsayilan=False
                )
            if yeni_yukleme_bilgisi["aktif"] != yukleme_aktif:
                onceki_sefer_id = aktif_sefer_id
                yukleme_aktif = yeni_yukleme_bilgisi["aktif"]
                aktif_sefer_id = yeni_yukleme_bilgisi["sefer_id"]
                son_araclar = []
                if yukleme_aktif:
                    aktif_sefer_yonu = sefer_yonunu_oku()
                    if aktif_sefer_id is None:
                        aktif_sefer_id = veritabani.sefer_baslat(
                            aktif_sefer_yonu
                        )
                        yukleme_durumunu_yaz(
                            True, sefer_id=aktif_sefer_id
                        )
                    tespit.oturumu_sifirla()
                    gecis_kontrol = GecisKontrol()
                    yaya_takip = YayaTakip(min_gorulme=3)
                    print(
                        "Yükleme başladı; geçiş kaydı aktif. "
                        f"Sefer yönü: {aktif_sefer_yonu}"
                    )
                else:
                    veritabani.sefer_bitir(onceki_sefer_id)
                    print("Yükleme bitti; geçiş kaydı durduruldu.")

            bugun = date.today()
            if bugun != son_rapor_gunu:
                try:
                    otomatik_excel_raporunu_guncelle(veritabani)
                    son_rapor_gunu = bugun
                except Exception as hata:
                    print("Gün değişimi Excel güncelleme hatası:", hata)

            # Her 3 karede bir YOLO çalıştır
            tespit_yapildi = (
                yukleme_aktif and kare_sayaci % KARE_ATLAMA == 0
            )

            if tespit_yapildi:

                bulunan_araclar = tespit.araclari_bul(kare)

                if bulunan_araclar is not None:
                    son_araclar = bulunan_araclar

                    yeni_yayalar = yaya_takip.guncelle(son_araclar, kare)
                    yaya_kaydedildi = False
                    for yaya in yeni_yayalar:
                        takip_id = yaya.get("id")
                        if veritabani.yaya_kaydet(
                            takip_id, aktif_sefer_yonu, aktif_sefer_id
                        ):
                            yaya_kaydedildi = True
                            print(f"Yaya yolcu sayildi -> ID {takip_id}")

                    if yaya_kaydedildi:
                        try:
                            otomatik_excel_raporunu_guncelle(veritabani)
                        except Exception as hata:
                            print("Yaya Excel guncelleme hatasi:", hata)
                    

            # Araç kutularını çiz
            for arac in son_araclar:
               
                arac_kutusunu_ciz(kare, arac)

            # Geçiş durumunu yalnızca güncel YOLO koordinatlarıyla ilerlet.
            # Atlanan karelerde eski kutuları yeniden kullanmak yanlış çizgi
            # geçişlerine neden olabilir.
            tamamlananlar = []

            if tespit_yapildi:
                guncel_araclar = [
                    nesne
                    for nesne in son_araclar
                    if nesne.get("sinif") != "Yaya Yolcu"
                ]
                tamamlananlar = gecis_kontrol.araclari_kontrol_et(
                    guncel_araclar,
                    kare
                ) or []

            # Feribota tamamen giren araçları kaydet
            for tamamlanan in tamamlananlar:

                arac_id = tamamlanan.get("id")

                arac = arac_bul(
                    son_araclar,
                    arac_id
                )

                if arac is None:
                    print(
                        f"ID {arac_id} için araç bilgisi bulunamadı."
                    )
                    continue

                kaydedilen_ucret = gecisi_kaydet(
                    veritabani=veritabani,
                    plaka_okuyucu=plaka_okuyucu,
                    ucret_sistemi=ucret_sistemi,
                    kare=kare,
                    arac=arac,
                    sefer_yonu=aktif_sefer_yonu,
                    sefer_id=aktif_sefer_id
                )

                if kaydedilen_ucret is not None:
                    try:
                        otomatik_excel_raporunu_guncelle(veritabani)
                    except Exception as hata:
                        print("Otomatik Excel güncelleme hatası:", hata)

            # Çizgileri çiz
            kare = gecis_kontrol.cizgileri_ciz(kare)

            # ==========================
            # FPS HESABI
            # ==========================
 
            simdiki_zaman = time.time()
            gecen_sure = simdiki_zaman - onceki_zaman
            onceki_zaman = simdiki_zaman

            if gecen_sure > 0:

                anlik_fps = 1 / gecen_sure

                if ortalama_fps == 0:
                    ortalama_fps = anlik_fps
                else:
                    ortalama_fps = (
                        ortalama_fps * 0.90
                        + anlik_fps * 0.10
                    )

            cv2.putText(
                kare,
                f"FPS: {ortalama_fps:.1f}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.putText(
                kare,
                (
                    "Toplam Arac: "
                    f"{gecis_kontrol.toplam_gecen_arac}"
                ),
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
               )
            cv2.putText(
                  kare,
                     f"Yaya Yolcu: {yaya_takip.toplam_yaya}",
                  (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                  0.8,
                 (0, 255, 255),
                 2
                )
            cv2.putText(
                kare,
                "YUKLEME AKTIF" if yukleme_aktif else "YUKLEME BEKLIYOR",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 200, 0) if yukleme_aktif else (0, 165, 255),
                2,
            )

            kare = video_kontrolleri.ciz(kare)

            cv2.imshow(
                PENCERE_ADI,
                kare
            )

            eylem = video_kontrolleri.eylemi_al()

            if eylem == "kayitlari_ac":
                try:
                    panel_sureci, yeni_acildi = yonetim_panelini_ac(
                        panel_sureci
                    )
                    mesaj = (
                        "Yonetim paneli acildi."
                        if yeni_acildi
                        else "Yonetim paneli zaten acik."
                    )
                    video_kontrolleri.mesaj_goster(mesaj)
                except Exception as hata:
                    video_kontrolleri.mesaj_goster(
                        f"Panel acilamadi: {hata}",
                        basarili=False
                    )

            tus = cv2.waitKey(1) & 0xFF

            if tus == ord("q"):
                print("Program kullanıcı tarafından kapatıldı.")
                break

            if not video_penceresi_acik_mi():
                print("Video penceresi kapatıldı.")
                break

    except KeyboardInterrupt:
        print("Program durduruldu.")

    except Exception as hata:
        print("=" * 60)
        print("ANA PROGRAM HATASI")
        print(type(hata).__name__, ":", hata)
        print("=" * 60)

    finally:

        if kamera is not None:
            kamera.release()

        if veritabani is not None:
            try:
                otomatik_excel_raporunu_guncelle(veritabani)
            except Exception as hata:
                print("Kapanış Excel güncelleme hatası:", hata)

            try:
                veritabani.baglantiyi_kapat()
                print("Veritabanı kayıtları korunarak kapatıldı.")
            except Exception as hata:
                print(
                    "Veritabanı kapatılırken hata:",
                    hata
                )

        cv2.destroyAllWindows()
        uygulama_kilidi.birak()

        print("Program kapatıldı.")


if __name__ == "__main__":
    ana_program()
