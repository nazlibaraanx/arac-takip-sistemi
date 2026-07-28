import sqlite3
import uuid
from datetime import datetime

from ayarlar import VERITABANI_YOLU
from sefer_yonu import (
    MALATYA_BASKIL,
    SEFER_YONLERI,
    sefer_yonunu_dogrula,
)


class Veritabani:

    def __init__(self, veritabani_yolu=VERITABANI_YOLU):
        self.oturum_id = uuid.uuid4().hex
        self.veritabani_yolu = veritabani_yolu

        self.baglanti = sqlite3.connect(
            veritabani_yolu,
            check_same_thread=False
        )

        self.imlec = self.baglanti.cursor()

        self.tablo_olustur()

    def tablo_olustur(self):

        # ==========================
        # GEÇİŞLER TABLOSU
        # ==========================

        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS gecisler(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            tarih TEXT,
            saat TEXT,

          takip_id INTEGER,

          plaka TEXT,

         arac_turu TEXT,

         genislik_px INTEGER,

         ucret REAL,
         sefer_yonu TEXT NOT NULL DEFAULT 'Malatya - Baskil'

        )
        """)

        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS seferler(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sefer_no TEXT NOT NULL UNIQUE,
            sefer_yonu TEXT NOT NULL,
            baslangic_tarihi TEXT NOT NULL,
            baslangic_saati TEXT NOT NULL,
            bitis_tarihi TEXT,
            bitis_saati TEXT,
            durum TEXT NOT NULL DEFAULT 'Aktif',
            toplam_arac INTEGER NOT NULL DEFAULT 0,
            toplam_yaya INTEGER NOT NULL DEFAULT 0,
            toplam_hasilat REAL NOT NULL DEFAULT 0,
            miras INTEGER NOT NULL DEFAULT 0
        )
        """)

        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT NOT NULL UNIQUE,
            sifre_ozeti TEXT NOT NULL,
            tuz TEXT NOT NULL,
            rol TEXT NOT NULL,
            aktif INTEGER NOT NULL DEFAULT 1,
            olusturulma TEXT NOT NULL
        )
        """)
        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS denetim_kayitlari(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zaman TEXT NOT NULL,
            kullanici TEXT NOT NULL,
            islem TEXT NOT NULL,
            ayrinti TEXT
        )
        """)

        self.imlec.execute("PRAGMA table_info(gecisler)")
        if "sefer_id" not in {satir[1] for satir in self.imlec.fetchall()}:
            self.imlec.execute(
                "ALTER TABLE gecisler ADD COLUMN sefer_id INTEGER"
            )

        # Günlük toplamlar oturum kayıtlarından bağımsız tutulur. Böylece
        # video kapanınca gecisler temizlense bile otomatik Excel raporu kalır.
        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS gunluk_ozetler(
            tarih TEXT NOT NULL,
            sefer_yonu TEXT NOT NULL DEFAULT 'Malatya - Baskil',
            toplam_arac INTEGER NOT NULL DEFAULT 0,
            toplam_yaya INTEGER NOT NULL DEFAULT 0,
            toplam_hasilat REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (tarih, sefer_yonu)
        )
        """)

        # Mevcut veritabanlarini veri kaybetmeden yeni yaya sutununa tasir.
        self.imlec.execute("PRAGMA table_info(gunluk_ozetler)")
        gunluk_sutunlari = {satir[1] for satir in self.imlec.fetchall()}
        if "toplam_yaya" not in gunluk_sutunlari:
            self.imlec.execute(
                "ALTER TABLE gunluk_ozetler "
                "ADD COLUMN toplam_yaya INTEGER NOT NULL DEFAULT 0"
            )

        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS yaya_gecisleri(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT,
            saat TEXT,
            takip_id INTEGER,
            oturum_id TEXT NOT NULL,
            sefer_yonu TEXT NOT NULL DEFAULT 'Malatya - Baskil',
            UNIQUE(oturum_id, takip_id)
        )
        """)

        # Eski sürümde takip_id bütün veritabanında UNIQUE idi. YOLO kimlikleri
        # her çalıştırmada yeniden başlayabildiğinden tekillik oturum bazında
        # uygulanır. Eski tablo veri kaybetmeden yeni şemaya taşınır.
        self.imlec.execute("PRAGMA table_info(yaya_gecisleri)")
        yaya_sutunlari = {satir[1] for satir in self.imlec.fetchall()}
        if "oturum_id" not in yaya_sutunlari:
            self.imlec.execute(
                "ALTER TABLE yaya_gecisleri RENAME TO yaya_gecisleri_eski"
            )
            self.imlec.execute("""
            CREATE TABLE yaya_gecisleri(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT,
                saat TEXT,
                takip_id INTEGER,
                oturum_id TEXT NOT NULL,
                sefer_yonu TEXT NOT NULL DEFAULT 'Malatya - Baskil',
                UNIQUE(oturum_id, takip_id)
            )
            """)
            self.imlec.execute("""
            INSERT INTO yaya_gecisleri(
                id, tarih, saat, takip_id, oturum_id, sefer_yonu
            )
            SELECT id, tarih, saat, takip_id, 'eski-' || id, ?
            FROM yaya_gecisleri_eski
            """, (MALATYA_BASKIL,))
            self.imlec.execute("DROP TABLE yaya_gecisleri_eski")

        self.imlec.execute("PRAGMA table_info(yaya_gecisleri)")
        if "sefer_id" not in {satir[1] for satir in self.imlec.fetchall()}:
            self.imlec.execute(
                "ALTER TABLE yaya_gecisleri ADD COLUMN sefer_id INTEGER"
            )

        # Grafik ekranındaki araç türü dağılımı da oturum kayıtları silinse
        # bile kalıcı olarak saklanır.
        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS gunluk_arac_turleri(
            tarih TEXT NOT NULL,
            sefer_yonu TEXT NOT NULL DEFAULT 'Malatya - Baskil',
            arac_turu TEXT NOT NULL,
            toplam_arac INTEGER NOT NULL DEFAULT 0,
            toplam_hasilat REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (tarih, sefer_yonu, arac_turu)
        )
        """)

        # Eski veritabanlarını veri kaybetmeden yön bazlı şemaya taşır.
        self._sefer_yonu_semasina_tasi()

        # Eski sürümden kalan mevcut geçişleri yalnızca ilk oluşturma sırasında
        # günlük özete taşı.
        self.imlec.execute("SELECT COUNT(*) FROM gunluk_ozetler")
        if self.imlec.fetchone()[0] == 0:
            self.imlec.execute("""
            INSERT INTO gunluk_ozetler
            (
                tarih,
                sefer_yonu,
                toplam_arac,
                toplam_hasilat
            )
            SELECT
                tarih,
                COALESCE(sefer_yonu, ?),
                COUNT(*),
                COALESCE(SUM(ucret), 0)
            FROM gecisler
            GROUP BY tarih, COALESCE(sefer_yonu, ?)
            """, (MALATYA_BASKIL, MALATYA_BASKIL))

        # Yeni grafik tablosu ilk kez oluşturulduğunda açık oturumdaki mevcut
        # kayıtları aktar. Sonraki açılışlarda kalıcı özetler korunur.
        self.imlec.execute("SELECT COUNT(*) FROM gunluk_arac_turleri")
        if self.imlec.fetchone()[0] == 0:
            self.imlec.execute("""
            INSERT INTO gunluk_arac_turleri
            (
                tarih,
                sefer_yonu,
                arac_turu,
                toplam_arac,
                toplam_hasilat
            )
            SELECT
                tarih,
                COALESCE(sefer_yonu, ?),
                arac_turu,
                COUNT(*),
                COALESCE(SUM(ucret), 0)
            FROM gecisler
            GROUP BY tarih, COALESCE(sefer_yonu, ?), arac_turu
            """, (MALATYA_BASKIL, MALATYA_BASKIL))

        self._miras_seferlerini_olustur()

        # ==========================
        # ÜCRETLER TABLOSU
        # ==========================

        self.imlec.execute("""
        CREATE TABLE IF NOT EXISTS ucretler(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            arac_turu TEXT NOT NULL,

            min_uzunluk REAL,

            max_uzunluk REAL,

            ucret REAL NOT NULL

        )
        """)

        # ==========================
        # VARSAYILAN TARİFE
        # ==========================

        self.imlec.execute("SELECT COUNT(*) FROM ucretler")

        if self.imlec.fetchone()[0] == 0:

            varsayilanlar = [

                ("Motosiklet", None, None, 75),
                ("Çapa", None, None, 180),
                ("Otomobil", None, None, 240),
                ("Toplu Taşıma", None, None, 280),
                ("Traktör Römorklu", None, None, 360),

                ("Kamyonet", 6.00, 7.00, 440),
                ("Kamyon", 7.01, 8.00, 550),
                ("Kamyon", 8.01, 9.00, 800),
                ("Kamyon", 9.01, 10.50, 1175),

                ("Uzun Araç", 10.51, 12.00, 1375),
                ("Uzun Araç", 12.01, 14.00, 1700),
                ("Uzun Araç", 14.01, 999.00, 1900)

            ]

            self.imlec.executemany(
                """
                INSERT INTO ucretler
                (
                    arac_turu,
                    min_uzunluk,
                    max_uzunluk,
                    ucret
                )
                VALUES
                (
                    ?, ?, ?, ?
                )
                """,
                varsayilanlar
            )

        self.baglanti.commit()
            # ==========================
    # GEÇİŞ KAYDET
    # ==========================

    def gecis_kaydet(
        self,
        takip_id,
        plaka,
        arac_turu,
        genislik_px,
        ucret,
        sefer_yonu=MALATYA_BASKIL,
        sefer_id=None
    ):
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        simdi = datetime.now()

        tarih = simdi.strftime("%d.%m.%Y")
        saat = simdi.strftime("%H:%M:%S")

        self.imlec.execute(
            """
            INSERT INTO gecisler
            (
                tarih,
                saat,
                takip_id,
                plaka,
                arac_turu,
                genislik_px,
                ucret,
                sefer_yonu,
                sefer_id
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                tarih,
                saat,
                takip_id,
                plaka,
                arac_turu,
                genislik_px,
                ucret,
                sefer_yonu,
                sefer_id
            )
        )

        self.imlec.execute(
            """
            INSERT INTO gunluk_ozetler
            (
                tarih,
                sefer_yonu,
                toplam_arac,
                toplam_hasilat
            )
            VALUES
            (
                ?, ?, 1, ?
            )
            ON CONFLICT(tarih, sefer_yonu) DO UPDATE SET
                toplam_arac = toplam_arac + 1,
                toplam_hasilat = toplam_hasilat + excluded.toplam_hasilat
            """,
            (
                tarih,
                sefer_yonu,
                ucret
            )
        )

        self.imlec.execute(
            """
            INSERT INTO gunluk_arac_turleri
            (
                tarih,
                sefer_yonu,
                arac_turu,
                toplam_arac,
                toplam_hasilat
            )
            VALUES
            (
                ?, ?, ?, 1, ?
            )
            ON CONFLICT(tarih, sefer_yonu, arac_turu) DO UPDATE SET
                toplam_arac = toplam_arac + 1,
                toplam_hasilat = toplam_hasilat + excluded.toplam_hasilat
            """,
            (
                tarih,
                sefer_yonu,
                arac_turu,
                ucret
            )
        )

        if sefer_id is not None:
            self.imlec.execute(
                """
                UPDATE seferler
                SET toplam_arac = toplam_arac + 1,
                    toplam_hasilat = toplam_hasilat + ?
                WHERE id = ? AND durum = 'Aktif'
                """,
                (ucret, int(sefer_id))
            )
            if self.imlec.rowcount == 0:
                raise ValueError("Aktif sefer bulunamadı; araç kaydı yapılamadı.")

        self.baglanti.commit()

    def _sefer_yonu_semasina_tasi(self):
        self.imlec.execute("PRAGMA table_info(gecisler)")
        if "sefer_yonu" not in {satir[1] for satir in self.imlec.fetchall()}:
            self.imlec.execute(
                "ALTER TABLE gecisler ADD COLUMN sefer_yonu TEXT "
                "NOT NULL DEFAULT 'Malatya - Baskil'"
            )

        self.imlec.execute("PRAGMA table_info(yaya_gecisleri)")
        if "sefer_yonu" not in {satir[1] for satir in self.imlec.fetchall()}:
            self.imlec.execute(
                "ALTER TABLE yaya_gecisleri ADD COLUMN sefer_yonu TEXT "
                "NOT NULL DEFAULT 'Malatya - Baskil'"
            )

        self.imlec.execute("PRAGMA table_info(gunluk_ozetler)")
        gunluk_bilgi = self.imlec.fetchall()
        gunluk_pk = [satir[1] for satir in gunluk_bilgi if satir[5]]
        if gunluk_pk != ["tarih", "sefer_yonu"]:
            self.imlec.execute(
                "ALTER TABLE gunluk_ozetler RENAME TO gunluk_ozetler_eski"
            )
            self.imlec.execute("""
            CREATE TABLE gunluk_ozetler(
                tarih TEXT NOT NULL,
                sefer_yonu TEXT NOT NULL,
                toplam_arac INTEGER NOT NULL DEFAULT 0,
                toplam_yaya INTEGER NOT NULL DEFAULT 0,
                toplam_hasilat REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (tarih, sefer_yonu)
            )
            """)
            eski_sutunlar = {satir[1] for satir in gunluk_bilgi}
            yon_ifadesi = (
                "COALESCE(sefer_yonu, ?)"
                if "sefer_yonu" in eski_sutunlar else "?"
            )
            self.imlec.execute(f"""
            INSERT INTO gunluk_ozetler
            (tarih, sefer_yonu, toplam_arac, toplam_yaya, toplam_hasilat)
            SELECT tarih, {yon_ifadesi}, toplam_arac,
                   COALESCE(toplam_yaya, 0), toplam_hasilat
            FROM gunluk_ozetler_eski
            """, (MALATYA_BASKIL,))
            self.imlec.execute("DROP TABLE gunluk_ozetler_eski")

        self.imlec.execute("PRAGMA table_info(gunluk_arac_turleri)")
        tur_bilgi = self.imlec.fetchall()
        tur_pk = [satir[1] for satir in tur_bilgi if satir[5]]
        if tur_pk != ["tarih", "sefer_yonu", "arac_turu"]:
            self.imlec.execute(
                "ALTER TABLE gunluk_arac_turleri "
                "RENAME TO gunluk_arac_turleri_eski"
            )
            self.imlec.execute("""
            CREATE TABLE gunluk_arac_turleri(
                tarih TEXT NOT NULL,
                sefer_yonu TEXT NOT NULL,
                arac_turu TEXT NOT NULL,
                toplam_arac INTEGER NOT NULL DEFAULT 0,
                toplam_hasilat REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (tarih, sefer_yonu, arac_turu)
            )
            """)
            eski_sutunlar = {satir[1] for satir in tur_bilgi}
            yon_ifadesi = (
                "COALESCE(sefer_yonu, ?)"
                if "sefer_yonu" in eski_sutunlar else "?"
            )
            self.imlec.execute(f"""
            INSERT INTO gunluk_arac_turleri
            (tarih, sefer_yonu, arac_turu, toplam_arac, toplam_hasilat)
            SELECT tarih, {yon_ifadesi}, arac_turu,
                   toplam_arac, toplam_hasilat
            FROM gunluk_arac_turleri_eski
            """, (MALATYA_BASKIL,))
            self.imlec.execute("DROP TABLE gunluk_arac_turleri_eski")

    def _miras_seferlerini_olustur(self):
        """Eski günlük özetleri birer korunmuş sefer kaydına bağlar."""

        self.imlec.execute("""
        SELECT tarih, sefer_yonu, toplam_arac, toplam_yaya, toplam_hasilat
        FROM gunluk_ozetler
        """)
        for tarih, yon, arac, yaya, hasilat in self.imlec.fetchall():
            etiket = "MB" if yon == MALATYA_BASKIL else "BM"
            tarih_metni = str(tarih)
            tarih_etiketi = (
                f"{tarih_metni[6:10]}{tarih_metni[3:5]}{tarih_metni[0:2]}"
            )
            sefer_no = f"ESKI-{tarih_etiketi}-{etiket}"
            self.imlec.execute(
                """
                INSERT OR IGNORE INTO seferler(
                    sefer_no, sefer_yonu, baslangic_tarihi, baslangic_saati,
                    bitis_tarihi, bitis_saati, durum,
                    toplam_arac, toplam_yaya, toplam_hasilat, miras
                )
                VALUES (?, ?, ?, '00:00:00', ?, '23:59:59', 'Tamamlandı',
                        ?, ?, ?, 1)
                """,
                (sefer_no, yon, tarih, tarih, arac, yaya, hasilat)
            )
            self.imlec.execute(
                "SELECT id FROM seferler WHERE sefer_no = ?",
                (sefer_no,)
            )
            sefer_id = self.imlec.fetchone()[0]
            self.imlec.execute(
                """
                UPDATE gecisler SET sefer_id = ?
                WHERE sefer_id IS NULL AND tarih = ? AND sefer_yonu = ?
                """,
                (sefer_id, tarih, yon)
            )
            self.imlec.execute(
                """
                UPDATE yaya_gecisleri SET sefer_id = ?
                WHERE sefer_id IS NULL AND tarih = ? AND sefer_yonu = ?
                """,
                (sefer_id, tarih, yon)
            )

    def sefer_baslat(self, sefer_yonu):
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        simdi = datetime.now()
        tarih = simdi.strftime("%d.%m.%Y")
        saat = simdi.strftime("%H:%M:%S")
        gun_etiketi = simdi.strftime("%Y%m%d")
        self.imlec.execute(
            """
            SELECT COUNT(*) FROM seferler
            WHERE baslangic_tarihi = ? AND miras = 0
            """,
            (tarih,)
        )
        sira = self.imlec.fetchone()[0] + 1
        while True:
            sefer_no = f"SF-{gun_etiketi}-{sira:03d}"
            try:
                self.imlec.execute(
                    """
                    INSERT INTO seferler(
                        sefer_no, sefer_yonu, baslangic_tarihi,
                        baslangic_saati, durum
                    )
                    VALUES (?, ?, ?, ?, 'Aktif')
                    """,
                    (sefer_no, sefer_yonu, tarih, saat)
                )
                break
            except sqlite3.IntegrityError:
                sira += 1
        self.baglanti.commit()
        return self.imlec.lastrowid

    def sefer_bitir(self, sefer_id):
        if sefer_id is None:
            return False
        simdi = datetime.now()
        self.imlec.execute(
            """
            UPDATE seferler
            SET bitis_tarihi = ?, bitis_saati = ?, durum = 'Tamamlandı'
            WHERE id = ? AND durum = 'Aktif'
            """,
            (
                simdi.strftime("%d.%m.%Y"),
                simdi.strftime("%H:%M:%S"),
                int(sefer_id),
            )
        )
        degisti = self.imlec.rowcount > 0
        self.baglanti.commit()
        return degisti

    def sefer_ozetlerini_getir(self):
        self.imlec.execute("""
        SELECT id, sefer_no, sefer_yonu, baslangic_tarihi, baslangic_saati,
               bitis_tarihi, bitis_saati, durum,
               toplam_arac, toplam_yaya, toplam_hasilat
        FROM seferler
        ORDER BY id DESC
        """)
        return self.imlec.fetchall()

    def sefer_plakalarini_getir(self, sefer_id):
        if sefer_id is None:
            return []
        self.imlec.execute(
            """
            SELECT DISTINCT plaka
            FROM gecisler
            WHERE sefer_id = ?
              AND plaka IS NOT NULL
              AND trim(plaka) != ''
              AND upper(trim(plaka)) != 'OKUNAMADI'
            """,
            (int(sefer_id),)
        )
        return [satir[0] for satir in self.imlec.fetchall()]

            # ==========================
    # TÜM GEÇİŞLERİ GETİR
    # ==========================

    def tum_gecisleri_getir(self):

        self.imlec.execute("""
        SELECT *
        FROM gecisler
        ORDER BY id DESC
        """)

        return self.imlec.fetchall()

    def gecis_ozetlerini_getir(self, sefer_yonu=MALATYA_BASKIL):
        """Yönetim paneli ve raporlar için gösterilecek alanları döndürür."""
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        self.imlec.execute("""
        SELECT
            id,
            tarih,
            saat,
            plaka,
            arac_turu,
            ucret
        FROM gecisler
        WHERE sefer_yonu = ?
        ORDER BY id DESC
        """, (sefer_yonu,))

        return self.imlec.fetchall()

    def gecis_ozetlerini_filtrele(
        self,
        baslangic_tarihi,
        bitis_tarihi,
        plaka="",
        sefer_yonu=MALATYA_BASKIL
    ):
        """Tarih aralığına ve isteğe bağlı plakaya göre kayıtları döndürür."""

        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        self.imlec.execute(
            """
            SELECT
                id,
                tarih,
                saat,
                plaka,
                arac_turu,
                ucret
            FROM gecisler
            WHERE
                substr(tarih, 7, 4) ||
                substr(tarih, 4, 2) ||
                substr(tarih, 1, 2)
                BETWEEN ? AND ?
              AND plaka LIKE ?
              AND sefer_yonu = ?
            ORDER BY id DESC
            """,
            (
                baslangic_tarihi.strftime("%Y%m%d"),
                bitis_tarihi.strftime("%Y%m%d"),
                f"%{plaka}%",
                sefer_yonu
            )
        )

        return self.imlec.fetchall()

    def gunluk_ozetleri_getir(self, sefer_yonu=MALATYA_BASKIL):
        """Kalıcı günlük araç ve hasılat toplamlarını kronolojik döndürür."""
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        self.imlec.execute("""
        SELECT
            tarih,
            toplam_arac,
            toplam_yaya,
            toplam_hasilat
        FROM gunluk_ozetler
        WHERE sefer_yonu = ?
        ORDER BY
            substr(tarih, 7, 4),
            substr(tarih, 4, 2),
            substr(tarih, 1, 2)
        """, (sefer_yonu,))

        return self.imlec.fetchall()

    def rapor_aylarini_getir(self, sefer_yonu=MALATYA_BASKIL):
        """Grafikli raporda seçilebilecek yıl ve ayları yeniden eskiye döndürür."""

        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        self.imlec.execute("""
        SELECT DISTINCT
            CAST(substr(tarih, 7, 4) AS INTEGER) AS yil,
            CAST(substr(tarih, 4, 2) AS INTEGER) AS ay
        FROM gunluk_ozetler
        WHERE length(tarih) = 10
          AND sefer_yonu = ?
        ORDER BY yil DESC, ay DESC
        """, (sefer_yonu,))

        return [
            (int(yil), int(ay))
            for yil, ay in self.imlec.fetchall()
        ]

    def tum_rapor_aylarini_getir(self):
        self.imlec.execute("""
        SELECT DISTINCT
            CAST(substr(tarih, 7, 4) AS INTEGER) AS yil,
            CAST(substr(tarih, 4, 2) AS INTEGER) AS ay
        FROM gunluk_ozetler
        WHERE length(tarih) = 10
        ORDER BY yil DESC, ay DESC
        """)
        return [(int(yil), int(ay)) for yil, ay in self.imlec.fetchall()]

    def aylik_grafik_ozeti_getir(
        self, yil, ay, sefer_yonu=MALATYA_BASKIL
    ):
        """Seçili ayın günlük toplamlarını ve araç türü dağılımını döndürür."""

        yil_metni = f"{int(yil):04d}"
        ay_metni = f"{int(ay):02d}"
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        self.imlec.execute(
            """
            SELECT
                tarih,
                toplam_arac,
                toplam_yaya,
                toplam_hasilat
            FROM gunluk_ozetler
            WHERE substr(tarih, 7, 4) = ?
              AND substr(tarih, 4, 2) = ?
              AND sefer_yonu = ?
            ORDER BY CAST(substr(tarih, 1, 2) AS INTEGER)
            """,
            (yil_metni, ay_metni, sefer_yonu)
        )
        gunluk_ozetler = self.imlec.fetchall()

        self.imlec.execute(
            """
            SELECT
                arac_turu,
                SUM(toplam_arac) AS arac_sayisi
            FROM gunluk_arac_turleri
            WHERE substr(tarih, 7, 4) = ?
              AND substr(tarih, 4, 2) = ?
              AND sefer_yonu = ?
            GROUP BY arac_turu
            ORDER BY arac_sayisi DESC, arac_turu
            """,
            (yil_metni, ay_metni, sefer_yonu)
        )
        arac_turleri = self.imlec.fetchall()

        return {
            "gunluk_ozetler": gunluk_ozetler,
            "arac_turleri": arac_turleri
        }

    def aylik_genel_grafik_ozeti_getir(self, yil, ay):
        """İki yönü birleştirerek seçili ayın grafik özetini döndürür."""

        yil_metni = f"{int(yil):04d}"
        ay_metni = f"{int(ay):02d}"
        self.imlec.execute(
            """
            SELECT tarih, SUM(toplam_arac), SUM(toplam_yaya),
                   SUM(toplam_hasilat)
            FROM gunluk_ozetler
            WHERE substr(tarih, 7, 4) = ?
              AND substr(tarih, 4, 2) = ?
            GROUP BY tarih
            ORDER BY CAST(substr(tarih, 1, 2) AS INTEGER)
            """,
            (yil_metni, ay_metni)
        )
        gunluk_ozetler = self.imlec.fetchall()
        self.imlec.execute(
            """
            SELECT arac_turu, SUM(toplam_arac) AS arac_sayisi
            FROM gunluk_arac_turleri
            WHERE substr(tarih, 7, 4) = ?
              AND substr(tarih, 4, 2) = ?
            GROUP BY arac_turu
            ORDER BY arac_sayisi DESC, arac_turu
            """,
            (yil_metni, ay_metni)
        )
        return {
            "gunluk_ozetler": gunluk_ozetler,
            "arac_turleri": self.imlec.fetchall(),
        }

    def aylik_yon_karsilastirmasi_getir(self, yil, ay):
        """İki yönün aylık toplamlarını ve günlük serilerini döndürür."""

        sonuc = {}
        for sefer_yonu in SEFER_YONLERI:
            ozet = self.aylik_grafik_ozeti_getir(yil, ay, sefer_yonu)
            gunlukler = ozet["gunluk_ozetler"]
            sonuc[sefer_yonu] = {
                "toplam_arac": sum(int(satir[1]) for satir in gunlukler),
                "toplam_yaya": sum(int(satir[2]) for satir in gunlukler),
                "toplam_hasilat": sum(float(satir[3]) for satir in gunlukler),
                "gunluk_ozetler": gunlukler,
            }
        return sonuc

    def sefer_grafik_ozeti_getir(self, sefer_id):
        """Tek bir yükleme seferinin rapor ve grafik özetini döndürür."""

        self.imlec.execute(
            """
            SELECT baslangic_tarihi, toplam_arac, toplam_yaya, toplam_hasilat
            FROM seferler WHERE id = ?
            """,
            (int(sefer_id),)
        )
        satir = self.imlec.fetchone()
        gunluk_ozetler = [satir] if satir else []
        self.imlec.execute(
            """
            SELECT arac_turu, COUNT(*)
            FROM gecisler
            WHERE sefer_id = ?
            GROUP BY arac_turu
            ORDER BY COUNT(*) DESC, arac_turu
            """,
            (int(sefer_id),)
        )
        return {
            "gunluk_ozetler": gunluk_ozetler,
            "arac_turleri": self.imlec.fetchall(),
        }

    def tarih_araligi_grafik_ozeti_getir(
        self, baslangic, bitis, sefer_yonu=MALATYA_BASKIL
    ):
        """Seçilen tarih aralığının grafik verilerini döndürür."""

        baslangic_metni = baslangic.strftime("%Y%m%d")
        bitis_metni = bitis.strftime("%Y%m%d")
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        tarih_ifadesi = (
            "substr(tarih, 7, 4) || "
            "substr(tarih, 4, 2) || "
            "substr(tarih, 1, 2)"
        )

        self.imlec.execute(
            f"""
            SELECT
                tarih,
                toplam_arac,
                toplam_yaya,
                toplam_hasilat
            FROM gunluk_ozetler
            WHERE {tarih_ifadesi} BETWEEN ? AND ?
              AND sefer_yonu = ?
            ORDER BY {tarih_ifadesi}
            """,
            (baslangic_metni, bitis_metni, sefer_yonu)
        )
        gunluk_ozetler = self.imlec.fetchall()

        self.imlec.execute(
            f"""
            SELECT
                arac_turu,
                SUM(toplam_arac) AS arac_sayisi
            FROM gunluk_arac_turleri
            WHERE {tarih_ifadesi} BETWEEN ? AND ?
              AND sefer_yonu = ?
            GROUP BY arac_turu
            ORDER BY arac_sayisi DESC, arac_turu
            """,
            (baslangic_metni, bitis_metni, sefer_yonu)
        )
        arac_turleri = self.imlec.fetchall()

        return {
            "gunluk_ozetler": gunluk_ozetler,
            "arac_turleri": arac_turleri
        }

    def tarih_araligi_yon_karsilastirmasi_getir(self, baslangic, bitis):
        """Tarih aralığında iki yönün özet, günlük seri ve sefer sayılarını verir."""

        baslangic_metni = baslangic.strftime("%Y%m%d")
        bitis_metni = bitis.strftime("%Y%m%d")
        tarih_ifadesi = (
            "substr(baslangic_tarihi, 7, 4) || "
            "substr(baslangic_tarihi, 4, 2) || "
            "substr(baslangic_tarihi, 1, 2)"
        )
        sonuc = {}
        for sefer_yonu in SEFER_YONLERI:
            ozet = self.tarih_araligi_grafik_ozeti_getir(
                baslangic, bitis, sefer_yonu
            )
            gunlukler = ozet["gunluk_ozetler"]
            self.imlec.execute(
                f"""
                SELECT COUNT(*)
                FROM seferler
                WHERE {tarih_ifadesi} BETWEEN ? AND ?
                  AND sefer_yonu = ?
                  AND miras = 0
                """,
                (baslangic_metni, bitis_metni, sefer_yonu)
            )
            sonuc[sefer_yonu] = {
                "toplam_arac": sum(int(satir[1]) for satir in gunlukler),
                "toplam_yaya": sum(int(satir[2]) for satir in gunlukler),
                "toplam_hasilat": sum(float(satir[3]) for satir in gunlukler),
                "sefer_sayisi": int(self.imlec.fetchone()[0]),
                "gunluk_ozetler": gunlukler,
                "arac_turleri": ozet["arac_turleri"],
            }
        return sonuc

    def yaya_kaydet(
        self, takip_id, sefer_yonu=MALATYA_BASKIL, sefer_id=None
    ):
        """Geçiş doğrulaması tamamlanan yayayı kalıcı olarak kaydeder."""
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        simdi = datetime.now()
        tarih = simdi.strftime("%d.%m.%Y")
        saat = simdi.strftime("%H:%M:%S")

        self.imlec.execute(
            """
            INSERT OR IGNORE INTO yaya_gecisleri(
                tarih, saat, takip_id, oturum_id, sefer_yonu, sefer_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                tarih, saat, takip_id, self.oturum_id, sefer_yonu, sefer_id
            )
        )
        if self.imlec.rowcount == 0:
            return False
        self.imlec.execute(
            """
            INSERT INTO gunluk_ozetler
            (tarih, sefer_yonu, toplam_arac, toplam_yaya, toplam_hasilat)
            VALUES (?, ?, 0, 1, 0)
            ON CONFLICT(tarih, sefer_yonu) DO UPDATE SET
                toplam_yaya = toplam_yaya + 1
            """,
            (tarih, sefer_yonu)
        )
        if sefer_id is not None:
            self.imlec.execute(
                """
                UPDATE seferler
                SET toplam_yaya = toplam_yaya + 1
                WHERE id = ? AND durum = 'Aktif'
                """,
                (int(sefer_id),)
            )
            if self.imlec.rowcount == 0:
                raise ValueError("Aktif sefer bulunamadı; yaya kaydı yapılamadı.")
        self.baglanti.commit()
        return True

    def toplam_yaya_sayisi(self, sefer_yonu=MALATYA_BASKIL):
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        self.imlec.execute(
            "SELECT COUNT(*) FROM yaya_gecisleri WHERE sefer_yonu = ?",
            (sefer_yonu,)
        )
        return self.imlec.fetchone()[0]

    # ==========================
    # BUGÜNKÜ GELİR
    # ==========================

    def bugunku_toplam_gelir(self, sefer_yonu=MALATYA_BASKIL):

        bugun = datetime.now().strftime("%d.%m.%Y")

        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        self.imlec.execute("""
        SELECT SUM(ucret)
        FROM gecisler
        WHERE tarih=? AND sefer_yonu=?
        """, (bugun, sefer_yonu))

        sonuc = self.imlec.fetchone()[0]

        return sonuc if sonuc else 0

    def bugunun_ozetini_getir(self, sefer_yonu=MALATYA_BASKIL):
        """Bugünün araç, yaya, hasılat ve son plaka bilgisini döndürür."""

        bugun = datetime.now().strftime("%d.%m.%Y")
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        self.imlec.execute(
            """
            SELECT toplam_arac, toplam_yaya, toplam_hasilat
            FROM gunluk_ozetler
            WHERE tarih = ? AND sefer_yonu = ?
            """,
            (bugun, sefer_yonu)
        )
        gunluk_satir = self.imlec.fetchone() or (0, 0, 0)

        self.imlec.execute(
            """
            SELECT plaka
            FROM gecisler
            WHERE tarih = ? AND sefer_yonu = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (bugun, sefer_yonu)
        )
        plaka_satiri = self.imlec.fetchone()
        son_plaka = (
            str(plaka_satiri[0]).strip()
            if plaka_satiri and plaka_satiri[0]
            else "Kayıt yok"
        )

        return {
            "toplam_arac": int(gunluk_satir[0]),
            "toplam_yaya": int(gunluk_satir[1]),
            "toplam_hasilat": float(gunluk_satir[2]),
            "son_plaka": son_plaka,
        }

    # ==========================
    # TOPLAM ARAÇ
    # ==========================

    def toplam_arac_sayisi(self, sefer_yonu=MALATYA_BASKIL):
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        self.imlec.execute("""
        SELECT COUNT(*)
        FROM gecisler
        WHERE sefer_yonu = ?
        """, (sefer_yonu,))

        return self.imlec.fetchone()[0]

    # ==========================
    # TÜM GEÇİŞLERİ SİL
    # ==========================

    def tum_gecisleri_sil(self):
        """Geçiş kayıtlarını siler; ücret tarifelerine dokunmaz."""

        self.imlec.execute("DELETE FROM gecisler")
        self.imlec.execute("DELETE FROM yaya_gecisleri")
        self.imlec.execute(
            "DELETE FROM sqlite_sequence WHERE name = ?",
            ("gecisler",)
        )
        self.imlec.execute(
            "DELETE FROM sqlite_sequence WHERE name = ?",
            ("yaya_gecisleri",)
        )
        self.baglanti.commit()

    def tum_rapor_verilerini_sil(self):
        """Oturum, aylik Excel ve grafik kaynaklarini sifirlar; tarifeleri korur."""

        self.imlec.execute("DELETE FROM gecisler")
        self.imlec.execute("DELETE FROM yaya_gecisleri")
        self.imlec.execute("DELETE FROM gunluk_ozetler")
        self.imlec.execute("DELETE FROM gunluk_arac_turleri")
        self.imlec.execute("DELETE FROM seferler")
        self.imlec.execute(
            "DELETE FROM sqlite_sequence WHERE name IN (?, ?, ?)",
            ("gecisler", "yaya_gecisleri", "seferler")
        )
        self.baglanti.commit()

    # ==========================
    # PLAKA ARA
    # ==========================

    def plaka_ara(self, plaka):

        self.imlec.execute(
            """
            SELECT *
            FROM gecisler
            WHERE plaka LIKE ?
            ORDER BY id DESC
            """,
            (f"%{plaka}%",)
        )

        return self.imlec.fetchall()

    def plaka_ozetlerini_ara(self, plaka, sefer_yonu=MALATYA_BASKIL):
        """Plakaya göre arar ve panelde gösterilecek alanları döndürür."""

        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)
        self.imlec.execute(
            """
            SELECT
                id,
                tarih,
                saat,
                plaka,
                arac_turu,
                ucret
            FROM gecisler
            WHERE plaka LIKE ?
              AND sefer_yonu = ?
            ORDER BY id DESC
            """,
            (f"%{plaka}%", sefer_yonu)
        )

        return self.imlec.fetchall()

    # ==========================
    # TOPLAM GELİR
    # ==========================

    def toplam_gelir(self, sefer_yonu=MALATYA_BASKIL):
        sefer_yonu = sefer_yonunu_dogrula(sefer_yonu)

        self.imlec.execute("""
        SELECT SUM(ucret)
        FROM gecisler
        WHERE sefer_yonu = ?
        """, (sefer_yonu,))

        sonuc = self.imlec.fetchone()[0]

        return sonuc if sonuc else 0

    # ==========================
    # ÜCRET GETİR
    # ==========================

    def ucret_getir(self, arac_turu, uzunluk_metre=None):
        """
        Araç türüne ve varsa fiziksel uzunluğa göre ücret döndürür.

        Uzunluk ölçülmemişse önce aralıksız genel tarife aranır. Genel
        tarife yoksa aynı araç türünün sıralı tarifelerinden orta kayıt
        seçilir; böylece SQL'deki ilk satırın rastgele kullanılması önlenir.
        """

        self.imlec.execute(
            """
            SELECT min_uzunluk, max_uzunluk, ucret
            FROM ucretler
            WHERE arac_turu = ?
            ORDER BY
                CASE
                    WHEN min_uzunluk IS NULL AND max_uzunluk IS NULL THEN 0
                    ELSE 1
                END,
                min_uzunluk
            """,
            (arac_turu,)
        )

        tarifeler = self.imlec.fetchall()

        if not tarifeler:
            return 0

        if uzunluk_metre is not None:
            for min_uzunluk, max_uzunluk, ucret in tarifeler:
                if min_uzunluk is None and max_uzunluk is None:
                    continue

                alt_sinir_uygun = (
                    min_uzunluk is None or uzunluk_metre >= min_uzunluk
                )
                ust_sinir_uygun = (
                    max_uzunluk is None or uzunluk_metre <= max_uzunluk
                )

                if alt_sinir_uygun and ust_sinir_uygun:
                    return ucret

        genel_tarife = next(
            (
                ucret
                for min_uzunluk, max_uzunluk, ucret in tarifeler
                if min_uzunluk is None and max_uzunluk is None
            ),
            None
        )

        if genel_tarife is not None:
            return genel_tarife

        if uzunluk_metre is not None:
            return 0

        sirali_ucretler = [ucret for _, _, ucret in tarifeler]
        return sirali_ucretler[len(sirali_ucretler) // 2]

    # ==========================
    # TÜM ÜCRETLER
    # ==========================

    def ucretleri_getir(self):

        self.imlec.execute("""
        SELECT
            id,
            arac_turu,
            min_uzunluk,
            max_uzunluk,
            ucret
        FROM ucretler
        ORDER BY id
        """)

        return self.imlec.fetchall()

    # ==========================
    # ÜCRET GÜNCELLE
    # ==========================

    def ucret_guncelle(self, id, yeni_ucret):

        self.imlec.execute(
            """
            UPDATE ucretler
            SET ucret = ?
            WHERE id = ?
            """,
            (
                yeni_ucret,
                id
            )
        )

        self.baglanti.commit()

    # ==========================
    # BAĞLANTIYI KAPAT
    # ==========================

    def baglantiyi_kapat(self):

        self.baglanti.close()

    def denetim_kaydi_ekle(self, kullanici, islem, ayrinti=""):
        self.imlec.execute(
            """
            INSERT INTO denetim_kayitlari(zaman, kullanici, islem, ayrinti)
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                str(kullanici or "sistem"),
                str(islem),
                str(ayrinti or ""),
            ),
        )
        self.baglanti.commit()

    def denetim_kayitlarini_getir(self, limit=200):
        self.imlec.execute(
            """
            SELECT zaman, kullanici, islem, ayrinti
            FROM denetim_kayitlari
            ORDER BY id DESC LIMIT ?
            """,
            (int(limit),),
        )
        return self.imlec.fetchall()

    def eski_plakalari_maskele(self, saklama_gunu=90, simdi=None):
        """Saklama süresi dolan plaka metinlerini, sayımları bozmadan siler."""

        simdi = simdi or datetime.now()
        sinir = simdi.date().toordinal() - int(saklama_gunu)
        self.imlec.execute(
            "SELECT id, tarih FROM gecisler WHERE plaka != 'SİLİNDİ'"
        )
        silinecekler = []
        for kimlik, tarih in self.imlec.fetchall():
            try:
                kayit_tarihi = datetime.strptime(tarih, "%d.%m.%Y").date()
            except (TypeError, ValueError):
                continue
            if kayit_tarihi.toordinal() < sinir:
                silinecekler.append((kimlik,))
        if silinecekler:
            self.imlec.executemany(
                "UPDATE gecisler SET plaka = 'SİLİNDİ' WHERE id = ?",
                silinecekler,
            )
            self.baglanti.commit()
        return len(silinecekler)
