import re
import cv2
import easyocr

from ayarlar import OCR_DILLERI, OCR_GUVEN


class PlakaOkuma:

    def __init__(self):
        print("Plaka okuma sistemi yükleniyor...")

        self.okuyucu = easyocr.Reader(
            OCR_DILLERI,
            gpu=False
        )

        print("Plaka okuma sistemi hazır.")


    def arac_bilgilerini_al(self, arac):
        """
        Araç sözlüğünden kutu koordinatlarını alır.
        """

        if not isinstance(arac, dict):
            return None

        kutu = arac.get("kutu")

        if kutu is None:
            kutu = arac.get("bbox")

        if kutu is None:
            x1 = arac.get("x1")
            y1 = arac.get("y1")
            x2 = arac.get("x2")
            y2 = arac.get("y2")

            if None in (x1, y1, x2, y2):
                return None

            kutu = [x1, y1, x2, y2]

        if len(kutu) < 4:
            return None

        x1, y1, x2, y2 = kutu[:4]

        return (
            int(x1),
            int(y1),
            int(x2),
            int(y2)
        )


    def arac_goruntusunu_kirp(self, kare, arac):
        """
        Tespit edilen aracın görüntüsünü kırpar.
        """

        koordinatlar = self.arac_bilgilerini_al(arac)

        if koordinatlar is None:
            return None

        x1, y1, x2, y2 = koordinatlar

        yukseklik, genislik = kare.shape[:2]

        x1 = max(0, min(x1, genislik - 1))
        x2 = max(0, min(x2, genislik))

        y1 = max(0, min(y1, yukseklik - 1))
        y2 = max(0, min(y2, yukseklik))

        if x2 <= x1 or y2 <= y1:
            return None

        arac_goruntusu = kare[y1:y2, x1:x2]

        if arac_goruntusu.size == 0:
            return None

        return arac_goruntusu


    def plaka_bolgesini_hazirla(self, arac_goruntusu):
        """
        Plakanın çoğunlukla bulunduğu aracın alt bölümünü alır
        ve OCR için görüntüyü hazırlar.
        """

        yukseklik, genislik = arac_goruntusu.shape[:2]

        # Plaka genellikle aracın alt yarısında bulunur.
        baslangic_y = int(yukseklik * 0.40)

        plaka_bolgesi = arac_goruntusu[
            baslangic_y:yukseklik,
            0:genislik
        ]

        if plaka_bolgesi.size == 0:
            return None

        # Küçük görüntüleri büyüt.
        plaka_bolgesi = cv2.resize(
            plaka_bolgesi,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        gri = cv2.cvtColor(
            plaka_bolgesi,
            cv2.COLOR_BGR2GRAY
        )

        gri = cv2.bilateralFilter(
            gri,
            9,
            75,
            75
        )

        esiklenmis = cv2.adaptiveThreshold(
            gri,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            7
        )

        return {
            "renkli": plaka_bolgesi,
            "gri": gri,
            "esiklenmis": esiklenmis
        }


    def metni_temizle(self, metin):
        """
        OCR sonucundaki boşluk ve özel karakterleri temizler.
        """

        if not metin:
            return ""

        metin = metin.upper()

        turkce_harfler = {
            "İ": "I",
            "Ş": "S",
            "Ğ": "G",
            "Ü": "U",
            "Ö": "O",
            "Ç": "C"
        }

        for eski, yeni in turkce_harfler.items():
            metin = metin.replace(eski, yeni)

        metin = re.sub(
            r"[^A-Z0-9]",
            "",
            metin
        )

        return metin


    def plaka_formati_uygun_mu(self, metin):
        """
        Türk plakalarına benzeyen metinleri kontrol eder.

        Örnek:
        44ABC123
        34AB1234
        06A12345
        """

        desen = r"^(0[1-9]|[1-7][0-9]|8[01])[A-Z]{1,3}[0-9]{2,5}$"

        return re.match(desen, metin) is not None


    def ocr_sonucunu_al(self, goruntu):
        """
        Tek bir görüntü üzerinde OCR çalıştırır.
        """

        sonuclar = self.okuyucu.readtext(
            goruntu,
            detail=1,
            paragraph=False,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

        bulunanlar = []

        for sonuc in sonuclar:

            if len(sonuc) < 3:
                continue

            _, metin, guven = sonuc

            temiz_metin = self.metni_temizle(metin)

            if len(temiz_metin) < 5 or float(guven) < OCR_GUVEN:
                continue

            bulunanlar.append({
                "metin": temiz_metin,
                "guven": float(guven)
            })

        return bulunanlar


    def en_iyi_sonucu_sec(self, sonuclar):
        """
        OCR sonuçlarından plakaya en çok benzeyeni seçer.
        """

        if not sonuclar:
            return None

        uygun_plakalar = []

        for sonuc in sonuclar:

            if self.plaka_formati_uygun_mu(
                sonuc["metin"]
            ):
                uygun_plakalar.append(sonuc)

        if uygun_plakalar:
            return max(
                uygun_plakalar,
                key=lambda sonuc: sonuc["guven"]
            )

        # Tam plaka formatı bulunamazsa en güvenilir sonucu döndür.
        return max(
            sonuclar,
            key=lambda sonuc: sonuc["guven"]
        )


    def plaka_oku(self, kare, arac):
        """
        Araç görüntüsünden plakayı okumaya çalışır.

        Dönen örnek:

        {
            "plaka": "44ABC123",
            "guven": 0.87,
            "basarili": True
        }
        """

        arac_goruntusu = self.arac_goruntusunu_kirp(
            kare,
            arac
        )

        if arac_goruntusu is None:
            return {
                "plaka": "OKUNAMADI",
                "guven": 0.0,
                "basarili": False
            }

        hazir_goruntuler = self.plaka_bolgesini_hazirla(
            arac_goruntusu
        )

        if hazir_goruntuler is None:
            return {
                "plaka": "OKUNAMADI",
                "guven": 0.0,
                "basarili": False
            }

        tum_sonuclar = []

        # Aynı bölgeyi üç farklı görüntü yöntemiyle okutuyoruz.
        for goruntu in hazir_goruntuler.values():

            sonuclar = self.ocr_sonucunu_al(
                goruntu
            )

            tum_sonuclar.extend(sonuclar)

        en_iyi_sonuc = self.en_iyi_sonucu_sec(
            tum_sonuclar
        )

        if en_iyi_sonuc is None:
            return {
                "plaka": "OKUNAMADI",
                "guven": 0.0,
                "basarili": False
            }

        plaka = en_iyi_sonuc["metin"]
        guven = en_iyi_sonuc["guven"]

        basarili = self.plaka_formati_uygun_mu(
            plaka
        )

        return {
            "plaka": plaka,
            "guven": guven,
            "basarili": basarili
        }
