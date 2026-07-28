import os
import shutil
import sqlite3
from datetime import datetime, timedelta

from ayarlar import VERITABANI_YOLU, YEDEK_KLASORU, YEDEK_SAKLAMA_GUNU


class OtomatikYedek:
    """SQLite veritabanının tutarlı günlük kopyalarını oluşturur."""

    @staticmethod
    def olustur(
        kaynak_yolu=VERITABANI_YOLU,
        hedef_klasor=YEDEK_KLASORU,
        baglanti=None,
        simdi=None,
        saklama_gunu=YEDEK_SAKLAMA_GUNU,
        zorla=False,
    ):
        simdi = simdi or datetime.now()
        os.makedirs(hedef_klasor, exist_ok=True)
        dosya_adi = f"feribot_yedek_{simdi:%Y-%m-%d}.db"
        hedef_yolu = os.path.join(hedef_klasor, dosya_adi)

        if (
            not zorla
            and os.path.exists(hedef_yolu)
            and os.path.getsize(hedef_yolu) > 0
        ):
            OtomatikYedek._eskileri_temizle(
                hedef_klasor, simdi, saklama_gunu
            )
            return hedef_yolu

        gecici_yol = hedef_yolu + ".tmp"
        kaynak_baglanti = baglanti
        baglantiyi_kapat = False
        if kaynak_baglanti is None:
            kaynak_baglanti = sqlite3.connect(kaynak_yolu)
            baglantiyi_kapat = True

        try:
            hedef_baglanti = sqlite3.connect(gecici_yol)
            try:
                kaynak_baglanti.backup(hedef_baglanti)
            finally:
                hedef_baglanti.close()
            os.replace(gecici_yol, hedef_yolu)
        finally:
            if baglantiyi_kapat:
                kaynak_baglanti.close()
            if os.path.exists(gecici_yol):
                os.remove(gecici_yol)

        OtomatikYedek._eskileri_temizle(hedef_klasor, simdi, saklama_gunu)
        return hedef_yolu

    @staticmethod
    def _eskileri_temizle(hedef_klasor, simdi, saklama_gunu):
        sinir = (simdi - timedelta(days=int(saklama_gunu))).date()
        for dosya_adi in os.listdir(hedef_klasor):
            if not (
                dosya_adi.startswith("feribot_yedek_")
                and dosya_adi.endswith(".db")
            ):
                continue
            try:
                tarih = datetime.strptime(
                    dosya_adi, "feribot_yedek_%Y-%m-%d.db"
                ).date()
            except ValueError:
                continue
            if tarih < sinir:
                os.remove(os.path.join(hedef_klasor, dosya_adi))

    @staticmethod
    def dogrula(yedek_yolu):
        if not os.path.isfile(yedek_yolu):
            raise FileNotFoundError("Yedek dosyası bulunamadı.")
        baglanti = sqlite3.connect(f"file:{yedek_yolu}?mode=ro", uri=True)
        try:
            sonuc = baglanti.execute("PRAGMA integrity_check").fetchone()[0]
            if str(sonuc).lower() != "ok":
                raise ValueError(f"Yedek bütünlük kontrolü başarısız: {sonuc}")
            tablolar = {
                satir[0]
                for satir in baglanti.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if "gecisler" not in tablolar:
                raise ValueError("Seçilen dosya feribot veritabanı değil.")
            return True
        finally:
            baglanti.close()

    @staticmethod
    def geri_yukle(yedek_yolu, hedef_yolu=VERITABANI_YOLU):
        """Kapalı veritabanına, mevcut dosyayı koruyarak güvenli geri yükleme yapar."""

        OtomatikYedek.dogrula(yedek_yolu)
        hedef_yolu = os.path.abspath(hedef_yolu)
        os.makedirs(os.path.dirname(hedef_yolu), exist_ok=True)
        guvenlik_kopyasi = None
        if os.path.exists(hedef_yolu):
            guvenlik_kopyasi = (
                hedef_yolu + f".geri_yukleme_oncesi_{datetime.now():%Y%m%d_%H%M%S}"
            )
            shutil.copy2(hedef_yolu, guvenlik_kopyasi)
        gecici = hedef_yolu + ".restore.tmp"
        try:
            shutil.copy2(yedek_yolu, gecici)
            OtomatikYedek.dogrula(gecici)
            os.replace(gecici, hedef_yolu)
        finally:
            if os.path.exists(gecici):
                os.remove(gecici)
        return hedef_yolu, guvenlik_kopyasi
