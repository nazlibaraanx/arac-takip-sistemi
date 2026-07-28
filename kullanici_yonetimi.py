import hashlib
import hmac
import os
from datetime import datetime


class KullaniciYonetimi:
    ROLLER = {"Yönetici", "Görevli", "Rapor Görüntüleyici"}

    def __init__(self, veritabani):
        self.vt = veritabani

    @staticmethod
    def _ozetle(sifre, tuz):
        return hashlib.pbkdf2_hmac(
            "sha256",
            str(sifre).encode("utf-8"),
            bytes.fromhex(tuz),
            210_000,
        ).hex()

    def kullanici_olustur(self, kullanici_adi, sifre, rol):
        kullanici_adi = str(kullanici_adi).strip()
        if len(kullanici_adi) < 3:
            raise ValueError("Kullanıcı adı en az 3 karakter olmalıdır.")
        if len(str(sifre)) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır.")
        if rol not in self.ROLLER:
            raise ValueError("Geçersiz kullanıcı rolü.")
        tuz = os.urandom(16).hex()
        ozet = self._ozetle(sifre, tuz)
        self.vt.imlec.execute(
            """
            INSERT INTO kullanicilar(
                kullanici_adi, sifre_ozeti, tuz, rol, olusturulma
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                kullanici_adi,
                ozet,
                tuz,
                rol,
                datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            ),
        )
        self.vt.baglanti.commit()
        self.vt.denetim_kaydi_ekle(
            "sistem", "Kullanıcı oluşturuldu", f"{kullanici_adi} · {rol}"
        )

    def giris_yap(self, kullanici_adi, sifre):
        self.vt.imlec.execute(
            """
            SELECT sifre_ozeti, tuz, rol
            FROM kullanicilar
            WHERE kullanici_adi = ? AND aktif = 1
            """,
            (str(kullanici_adi).strip(),),
        )
        kayit = self.vt.imlec.fetchone()
        if not kayit:
            return None
        beklenen, tuz, rol = kayit
        bulunan = self._ozetle(sifre, tuz)
        if not hmac.compare_digest(beklenen, bulunan):
            self.vt.denetim_kaydi_ekle(
                kullanici_adi, "Başarısız giriş"
            )
            return None
        self.vt.denetim_kaydi_ekle(kullanici_adi, "Giriş başarılı")
        return {"kullanici_adi": kullanici_adi, "rol": rol}
