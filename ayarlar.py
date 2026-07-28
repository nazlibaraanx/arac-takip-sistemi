"""
===========================================
AKILLI OTOYOL GEÇİŞ SİSTEMİ
Ayarlar Dosyası
===========================================
Bu dosya sistemin tüm ayarlarını içerir.
Diğer dosyalar buradan bilgi alacaktır.
"""

import os

# ===========================================
# KLASÖRLER
# ===========================================

PROJE_KLASORU = os.path.dirname(os.path.abspath(__file__))

VERITABANI_YOLU = os.path.join(PROJE_KLASORU, "feribot.db")

VIDEO_KLASORU = os.path.join(PROJE_KLASORU, "videolar")

MODEL_KLASORU = os.path.join(PROJE_KLASORU, "modeller")

CIKTI_KLASORU = os.path.join(PROJE_KLASORU, "ciktilar")

RAPOR_KLASORU = os.path.join(PROJE_KLASORU, "raporlar")

LOG_KLASORU = os.path.join(PROJE_KLASORU, "loglar")

YEDEK_KLASORU = os.path.join(PROJE_KLASORU, "yedekler")

YEDEK_SAKLAMA_GUNU = 30


# ===========================================
# DOSYA YOLLARI
# ===========================================

VIDEO_YOLU = os.path.join(VIDEO_KLASORU, "kayit.mp4")

MODEL_YOLU = os.path.join(MODEL_KLASORU, "yolov8m.pt")

CIKTI_VIDEO = os.path.join(CIKTI_KLASORU, "sonuc.mp4")

RAPOR_DOSYASI = os.path.join(RAPOR_KLASORU, "gecisler.csv")


# ===========================================
# YOLO AYARLARI
# ===========================================

GORUNTU_BOYUTU = 640

GUVEN_ESIGI = 0.45

TAKIP_KALICILIK = True

# Servis/minibüs COCO veri kümesinde ayrı bir sınıf değildir. Girişe yaklaşmış,
# dar ve yüksek kamyon/otobüs kutuları servis olarak düzeltilir.
SERVIS_DUZELTME_AKTIF = True
# COCO modelinin "car" dediği otomobilleri yalnızca kutu oranıyla minibüse
# çevirmek önden yaklaşan otomobillerde yanlış sonuç üretebilir. Özel feribot
# modeli eğitilene kadar otomobil dönüşümü kapalı tutulur; truck/bus kanıtları
# yine toplu taşıma olarak değerlendirilebilir.
SERVIS_OTOMOBIL_DUZELTME_AKTIF = False
SERVIS_MIN_ALT_Y_ORANI = 0.45
SERVIS_MAKS_GENISLIK_ORANI = 0.22
SERVIS_MIN_BOY_EN_ORANI = 0.90
# Modelin `car` dediği minibüsleri düzeltirken normal otomobilleri korumak için
# kullanılan daha dar üst sınır.
SERVIS_OTOMOBIL_MAKS_GENISLIK_ORANI = 0.21

# Önden görünen, otomobil gövde oranındaki araçları modelin anlık truck/bus
# sıçramalarından korur. Bu kural takip kimliğine veya video dosyasına bağlı
# değildir; aynı fiziksel orandaki bütün araçlarda uygulanır.
OTOMOBIL_BOYUT_DUZELTME_AKTIF = True
OTOMOBIL_MIN_ALT_Y_ORANI = 0.45
OTOMOBIL_MIN_GENISLIK_ORANI = 0.08
OTOMOBIL_MAKS_GENISLIK_ORANI = 0.30
OTOMOBIL_MAKS_BOY_EN_ORANI = 1.05

# Kameraya yaklaşınca görüntünün büyük bölümünü kaplayan geniş minibüs/servis
# gövdelerini otomobilden ayırır.
TOPLU_TASIMA_GENIS_GOVDE_AKTIF = True
TOPLU_TASIMA_GENIS_GOVDE_MIN_ALT_Y_ORANI = 0.45
TOPLU_TASIMA_GENIS_GOVDE_MIN_GENISLIK_ORANI = 0.30
TOPLU_TASIMA_GENIS_GOVDE_MAKS_BOY_EN_ORANI = 0.90


# ===========================================
# GEÇİŞ ÇİZGİLERİ
# ===========================================

GECIS_SOL_X_ORANI = 0.38
GECIS_SAG_X_ORANI = 0.90


# ===========================================
# OCR AYARLARI
# ===========================================

OCR_DILLERI = ['tr', 'en']

OCR_GUVEN = 0.35


# ===========================================
# ARAÇ SINIFLARI
# ===========================================

ARAC_SINIFLARI = [
    "Motosiklet",
    "Çapa",
    "Otomobil",
    "Toplu Taşıma",
    "Traktör Römorklu",
    "Kamyonet",
    "Kamyon",
    "Uzun Araç"

]

# Takip kimlikleri her video/kamera oturumunda yeniden üretildiği için burada
# kimliğe bağlı kalıcı düzeltme tutulmaz. Özel bir kayıt incelenirken geçici
# düzeltme gerekiyorsa bu sözlük yalnızca o kayıt için doldurulmalıdır.
ARAC_ID_SINIF_DUZELTMELERI = {}

# ===========================================
# ÜCRETLER
# ===========================================

UCRETLER = {

    "Motosiklet": 75,

    "Çapa": 180,

    "Otomobil": 240,

    "Toplu Taşıma": 280,

    "Traktör Römorklu": 360,

    "Kamyonet": 440,

    "Kamyon": 800,

    "Uzun Araç": 1900

}


# ===========================================
# RENKLER (BGR)
# ===========================================

YESIL = (0,255,0)

KIRMIZI = (0,0,255)

MAVI = (255,0,0)

SARI = (0,255,255)

BEYAZ = (255,255,255)

SIYAH = (0,0,0)


# ===========================================
# YAZI TİPİ
# ===========================================

YAZI_TIPI = 0


# ===========================================
# ARAYÜZ
# ===========================================

PANEL_GENISLIK = 350

FPS_GOSTER = True

HASILAT_GOSTER = True

PLAKA_GOSTER = True

ID_GOSTER = True
