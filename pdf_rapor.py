import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from sefer_yonu import MALATYA_BASKIL


class PdfRapor:

    AY_ADLARI = {
        1: "Ocak",
        2: "Şubat",
        3: "Mart",
        4: "Nisan",
        5: "Mayıs",
        6: "Haziran",
        7: "Temmuz",
        8: "Ağustos",
        9: "Eylül",
        10: "Ekim",
        11: "Kasım",
        12: "Aralık"
    }

    ARAC_ISIMLERI = {
        "car": "Otomobil",
        "truck": "Kamyon",
        "bus": "Toplu Taşıma",
        "motorcycle": "Motosiklet",
        "minibus": "Toplu Taşıma",
        "Otobüs": "Toplu Taşıma",
        "Servis": "Toplu Taşıma",
        "Minibüs": "Toplu Taşıma"
    }

    LACIVERT = colors.HexColor("#17365D")
    MAVI = colors.HexColor("#2F75B5")
    ACIK_MAVI = colors.HexColor("#EAF2F8")
    CIZGI = colors.HexColor("#D9E2F3")
    METIN = colors.HexColor("#27364A")
    IKINCIL_METIN = colors.HexColor("#667085")
    GRAFIK_RENKLERI = [
        colors.HexColor("#2F75B5"),
        colors.HexColor("#70AD47"),
        colors.HexColor("#ED7D31"),
        colors.HexColor("#A5A5A5"),
        colors.HexColor("#5B9BD5"),
        colors.HexColor("#FFC000"),
        colors.HexColor("#8064A2"),
        colors.HexColor("#4BACC6")
    ]

    @classmethod
    def _fontlari_yukle(cls):
        if "RaporNormal" in pdfmetrics.getRegisteredFontNames():
            return

        windows_klasoru = os.environ.get("WINDIR", r"C:\Windows")
        normal_yolu = os.path.join(windows_klasoru, "Fonts", "arial.ttf")
        kalin_yolu = os.path.join(windows_klasoru, "Fonts", "arialbd.ttf")

        if os.path.exists(normal_yolu) and os.path.exists(kalin_yolu):
            pdfmetrics.registerFont(TTFont("RaporNormal", normal_yolu))
            pdfmetrics.registerFont(TTFont("RaporKalin", kalin_yolu))
        else:
            # Windows dışındaki test ortamlarında ASCII metinler için güvenli
            # bir geri dönüş sağlar.
            pdfmetrics.registerFont(
                TTFont(
                    "RaporNormal",
                    os.path.join(os.path.dirname(__file__), "arial.ttf")
                )
            )

    @staticmethod
    def _para_bicimlendir(deger):
        return (
            f"{float(deger):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
            + " TL"
        )

    @classmethod
    def _ozet_karti_ciz(cls, pdf, x, y, genislik, baslik, deger):
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(cls.CIZGI)
        pdf.roundRect(x, y, genislik, 64, 6, fill=1, stroke=1)
        pdf.setFillColor(cls.IKINCIL_METIN)
        pdf.setFont("RaporNormal", 9)
        pdf.drawString(x + 14, y + 43, baslik)
        pdf.setFillColor(cls.LACIVERT)
        pdf.setFont("RaporKalin", 16)
        pdf.drawString(x + 14, y + 17, deger)

    @classmethod
    def _gunluk_grafigi_ciz(
        cls, pdf, x, y, genislik, yukseklik, veriler, grafik_modu="arac"
    ):
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(cls.CIZGI)
        pdf.roundRect(x, y, genislik, yukseklik, 6, fill=1, stroke=1)
        pdf.setFillColor(cls.LACIVERT)
        pdf.setFont("RaporKalin", 11)
        yaya_modu = grafik_modu == "yaya"
        pdf.drawString(
            x + 16,
            y + yukseklik - 24,
            "Günlük Yaya Yolcu Sayısı" if yaya_modu else "Günlük Araç Geçişleri"
        )

        if not veriler:
            pdf.setFillColor(cls.IKINCIL_METIN)
            pdf.setFont("RaporNormal", 10)
            pdf.drawCentredString(
                x + genislik / 2,
                y + yukseklik / 2,
                "Bu ay için henüz geçiş kaydı yok."
            )
            return

        sol, sag, alt, ust = 42, 16, 34, 46
        alan_x = x + sol
        alan_y = y + alt
        alan_genisligi = genislik - sol - sag
        alan_yuksekligi = yukseklik - alt - ust
        veri_indeksi = 2 if yaya_modu else 1
        sayilar = [int(satir[veri_indeksi]) for satir in veriler]
        en_yuksek = max(max(sayilar), 1)
        eksen_ust = max(5, ((en_yuksek + 4) // 5) * 5)

        pdf.setFont("RaporNormal", 7)
        for oran in (0, 0.5, 1):
            deger = int(eksen_ust * oran)
            cizgi_y = alan_y + alan_yuksekligi * oran
            pdf.setStrokeColor(cls.CIZGI)
            pdf.line(alan_x, cizgi_y, alan_x + alan_genisligi, cizgi_y)
            pdf.setFillColor(cls.IKINCIL_METIN)
            pdf.drawRightString(alan_x - 7, cizgi_y - 2, str(deger))

        adet = len(veriler)
        dilim = alan_genisligi / adet
        cubuk_genisligi = max(3, min(18, dilim * 0.48))
        etiket_adimi = max(1, (adet + 9) // 10)

        for indeks, satir in enumerate(veriler):
            tarih = satir[0]
            sayi = int(satir[veri_indeksi])
            merkez_x = alan_x + dilim * indeks + dilim / 2
            cubuk_yuksekligi = alan_yuksekligi * sayi / eksen_ust
            pdf.setFillColor(
                colors.HexColor("#ED7D31") if yaya_modu else cls.MAVI
            )
            pdf.rect(
                merkez_x - cubuk_genisligi / 2,
                alan_y,
                cubuk_genisligi,
                cubuk_yuksekligi,
                fill=1,
                stroke=0
            )

            if indeks % etiket_adimi == 0 or indeks == adet - 1:
                pdf.setFillColor(cls.IKINCIL_METIN)
                pdf.setFont("RaporNormal", 7)
                pdf.drawCentredString(merkez_x, alan_y - 13, str(tarih)[:2])

    @classmethod
    def _tur_grafigi_ciz(cls, pdf, x, y, genislik, yukseklik, veriler):
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(cls.CIZGI)
        pdf.roundRect(x, y, genislik, yukseklik, 6, fill=1, stroke=1)
        pdf.setFillColor(cls.LACIVERT)
        pdf.setFont("RaporKalin", 11)
        pdf.drawString(x + 16, y + yukseklik - 24, "Araç Türü Dağılımı")

        if not veriler:
            pdf.setFillColor(cls.IKINCIL_METIN)
            pdf.setFont("RaporNormal", 10)
            pdf.drawCentredString(
                x + genislik / 2,
                y + yukseklik / 2,
                "Bu ay için araç türü verisi yok."
            )
            return

        duzeltilmis = [
            (cls.ARAC_ISIMLERI.get(tur, tur), int(sayi))
            for tur, sayi in veriler
        ]
        toplam = sum(sayi for _, sayi in duzeltilmis) or 1
        en_yuksek = max(sayi for _, sayi in duzeltilmis) or 1
        satir_yuksekligi = min(29, (yukseklik - 54) / len(duzeltilmis))
        etiket_genisligi = 92
        cubuk_x = x + etiket_genisligi
        cubuk_genisligi = genislik - etiket_genisligi - 52

        for indeks, (tur, sayi) in enumerate(duzeltilmis):
            merkez_y = y + yukseklik - 50 - indeks * satir_yuksekligi
            renk = cls.GRAFIK_RENKLERI[indeks % len(cls.GRAFIK_RENKLERI)]
            yuzde = sayi / toplam * 100

            pdf.setFillColor(cls.METIN)
            pdf.setFont("RaporNormal", 7.5)
            pdf.drawRightString(cubuk_x - 7, merkez_y + 2, tur)
            pdf.setFillColor(colors.HexColor("#EEF2F6"))
            pdf.rect(cubuk_x, merkez_y - 2, cubuk_genisligi, 9, fill=1, stroke=0)
            pdf.setFillColor(renk)
            pdf.rect(
                cubuk_x,
                merkez_y - 2,
                cubuk_genisligi * sayi / en_yuksek,
                9,
                fill=1,
                stroke=0
            )
            pdf.setFillColor(cls.METIN)
            pdf.setFont("RaporKalin", 7.5)
            pdf.drawRightString(
                x + genislik - 12,
                merkez_y + 1,
                f"{sayi} - %{yuzde:.0f}"
            )

    @classmethod
    def olustur(
        cls,
        dosya_yolu,
        yil,
        ay,
        gunluk_ozetler,
        arac_turleri,
        grafik_modu="arac",
        ornek=False,
        sefer_yonu=MALATYA_BASKIL
    ):
        cls._fontlari_yukle()
        os.makedirs(os.path.dirname(os.path.abspath(dosya_yolu)), exist_ok=True)

        pdf = canvas.Canvas(dosya_yolu, pagesize=landscape(A4))
        sayfa_genisligi, sayfa_yuksekligi = landscape(A4)
        pdf.setTitle(
            f"{sefer_yonu} - {cls.AY_ADLARI[int(ay)]} {int(yil)} Feribot Raporu"
        )
        pdf.setAuthor("Akıllı Feribot Geçiş Sistemi")

        pdf.setFillColor(colors.HexColor("#F4F7FA"))
        pdf.rect(0, 0, sayfa_genisligi, sayfa_yuksekligi, fill=1, stroke=0)
        pdf.setFillColor(cls.LACIVERT)
        pdf.rect(0, sayfa_yuksekligi - 62, sayfa_genisligi, 62, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("RaporKalin", 18)
        pdf.drawString(
            32,
            sayfa_yuksekligi - 38,
            f"{cls.AY_ADLARI[int(ay)]} {int(yil)} Feribot Geçiş Raporu"
        )
        pdf.setFont("RaporNormal", 9)
        pdf.drawRightString(
            sayfa_genisligi - 32,
            sayfa_yuksekligi - 36,
            (
                "Aylık Grafik Özeti - Örnek Veriler"
                if ornek
                else f"{sefer_yonu} · Aylık Grafik Özeti"
            )
        )

        toplam_arac = sum(int(satir[1]) for satir in gunluk_ozetler)
        toplam_yaya = sum(int(satir[2]) for satir in gunluk_ozetler)
        toplam_hasilat = sum(float(satir[3]) for satir in gunluk_ozetler)
        yaya_modu = grafik_modu == "yaya"
        yogun_indeksi = 2 if yaya_modu else 1
        if gunluk_ozetler:
            yogun_satir = max(
                gunluk_ozetler,
                key=lambda satir: int(satir[yogun_indeksi])
            )
            yogun_tarih = yogun_satir[0]
            yogun_sayi = yogun_satir[yogun_indeksi]
            yogun_gun = int(str(yogun_tarih)[:2])
            yogun_metin = (
                f"{yogun_gun} {cls.AY_ADLARI[int(ay)]} - "
                f"{int(yogun_sayi)} {'yaya yolcu' if yaya_modu else 'araç'}"
            )
        else:
            yogun_metin = "Kayıt yok"

        kenar = 32
        kart_aralik = 12
        kart_sayisi = 2 if yaya_modu else 3
        kart_genisligi = (
            sayfa_genisligi - kenar * 2 - kart_aralik * (kart_sayisi - 1)
        ) / kart_sayisi
        kart_y = sayfa_yuksekligi - 145
        if yaya_modu:
            cls._ozet_karti_ciz(
                pdf, kenar, kart_y, kart_genisligi,
                "Yaya Yolcu", f"{toplam_yaya:,}".replace(",", ".")
            )
        else:
            cls._ozet_karti_ciz(
                pdf, kenar, kart_y, kart_genisligi,
                "Toplam Araç", f"{toplam_arac:,}".replace(",", ".")
            )
            cls._ozet_karti_ciz(
                pdf, kenar + kart_genisligi + kart_aralik, kart_y,
                kart_genisligi, "Toplam Hasılat",
                cls._para_bicimlendir(toplam_hasilat)
            )
        cls._ozet_karti_ciz(
            pdf,
            kenar + (kart_genisligi + kart_aralik) * (kart_sayisi - 1),
            kart_y,
            kart_genisligi,
            "En Yoğun Yaya Günü" if yaya_modu else "En Yoğun Araç Günü",
            yogun_metin
        )

        grafik_y = 62
        grafik_yuksekligi = kart_y - grafik_y - 18
        sol_genislik = (
            sayfa_genisligi - kenar * 2 if yaya_modu else 490
        )
        cls._gunluk_grafigi_ciz(
            pdf,
            kenar,
            grafik_y,
            sol_genislik,
            grafik_yuksekligi,
            gunluk_ozetler,
            grafik_modu=grafik_modu
        )
        if not yaya_modu:
            cls._tur_grafigi_ciz(
                pdf,
                kenar + sol_genislik + 14,
                grafik_y,
                sayfa_genisligi - kenar * 2 - sol_genislik - 14,
                grafik_yuksekligi,
                arac_turleri
            )

        pdf.setFillColor(cls.IKINCIL_METIN)
        pdf.setFont("RaporNormal", 7.5)
        pdf.drawString(
            kenar,
            31,
            "Kaynak: Akıllı Feribot Geçiş Sistemi veritabanı"
        )
        pdf.drawRightString(
            sayfa_genisligi - kenar,
            31,
            f"Oluşturulma: {datetime.now():%d.%m.%Y %H:%M}"
        )

        pdf.showPage()
        pdf.save()
        return dosya_yolu

    @classmethod
    def tarih_araligi_olustur(
        cls,
        dosya_yolu,
        baslangic,
        bitis,
        gunluk_ozetler,
        grafik_modu="arac",
        sefer_yonu=MALATYA_BASKIL
    ):
        """Seçili tarih aralığını tek seri günlük grafik olarak PDF'e yazar."""

        cls._fontlari_yukle()
        os.makedirs(os.path.dirname(os.path.abspath(dosya_yolu)), exist_ok=True)
        pdf = canvas.Canvas(dosya_yolu, pagesize=landscape(A4))
        genislik, yukseklik = landscape(A4)
        pdf.setTitle(f"{sefer_yonu} - Seçilen Tarih Aralığı Feribot Raporu")
        pdf.setAuthor("Akıllı Feribot Geçiş Sistemi")

        pdf.setFillColor(colors.HexColor("#F6F8FB"))
        pdf.rect(0, 0, genislik, yukseklik, fill=1, stroke=0)
        pdf.setFillColor(cls.LACIVERT)
        pdf.rect(0, yukseklik - 62, genislik, 62, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("RaporKalin", 17)
        pdf.drawString(32, yukseklik - 37, "Tarih Aralığı Geçiş Raporu")
        pdf.setFont("RaporNormal", 9)
        pdf.drawRightString(
            genislik - 32,
            yukseklik - 36,
            (
                f"{sefer_yonu} · "
                f"{baslangic:%d.%m.%Y} - {bitis:%d.%m.%Y}"
            )
        )

        toplam_arac = sum(int(satir[1]) for satir in gunluk_ozetler)
        toplam_yaya = sum(int(satir[2]) for satir in gunluk_ozetler)
        toplam_hasilat = sum(float(satir[3]) for satir in gunluk_ozetler)
        kenar = 32
        kart_aralik = 14
        kart_genisligi = (genislik - kenar * 2 - kart_aralik * 2) / 3
        kart_y = yukseklik - 145
        cls._ozet_karti_ciz(
            pdf, kenar, kart_y, kart_genisligi,
            "Toplam Araç", f"{toplam_arac:,}".replace(",", ".")
        )
        cls._ozet_karti_ciz(
            pdf, kenar + kart_genisligi + kart_aralik, kart_y,
            kart_genisligi, "Yaya Yolcu",
            f"{toplam_yaya:,}".replace(",", ".")
        )
        cls._ozet_karti_ciz(
            pdf, kenar + (kart_genisligi + kart_aralik) * 2, kart_y,
            kart_genisligi, "Toplam Hasılat",
            cls._para_bicimlendir(toplam_hasilat)
        )

        grafik_x, grafik_y = kenar, 62
        grafik_w = genislik - kenar * 2
        grafik_h = kart_y - grafik_y - 18
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(cls.CIZGI)
        pdf.roundRect(grafik_x, grafik_y, grafik_w, grafik_h, 6, fill=1, stroke=1)
        yaya_modu = grafik_modu == "yaya"
        veri_indeksi = 2 if yaya_modu else 1
        baslik = "Günlük Yaya Yolcu Sayısı" if yaya_modu else "Günlük Araç Geçişleri"
        renk = colors.HexColor("#C98762" if yaya_modu else "#5F829E")
        pdf.setFillColor(cls.LACIVERT)
        pdf.setFont("RaporKalin", 11)
        pdf.drawString(grafik_x + 16, grafik_y + grafik_h - 24, baslik)

        sol, sag, alt, ust = 44, 18, 38, 46
        alan_x = grafik_x + sol
        alan_y = grafik_y + alt
        alan_w = grafik_w - sol - sag
        alan_h = grafik_h - alt - ust
        sayilar = [int(satir[veri_indeksi]) for satir in gunluk_ozetler]
        en_yuksek = max(max(sayilar, default=0), 1)
        eksen_ust = max(5, ((en_yuksek + 4) // 5) * 5)
        for oran in (0, 0.5, 1):
            y = alan_y + alan_h * oran
            pdf.setStrokeColor(cls.CIZGI)
            pdf.line(alan_x, y, alan_x + alan_w, y)
            pdf.setFillColor(cls.IKINCIL_METIN)
            pdf.setFont("RaporNormal", 7)
            pdf.drawRightString(alan_x - 7, y - 2, str(int(eksen_ust * oran)))

        if gunluk_ozetler:
            dilim = alan_w / len(gunluk_ozetler)
            cubuk_w = max(3, min(20, dilim * 0.5))
            for indeks, satir in enumerate(gunluk_ozetler):
                x = alan_x + dilim * indeks + dilim / 2
                deger = int(satir[veri_indeksi])
                cubuk_h = alan_h * deger / eksen_ust
                pdf.setFillColor(renk)
                pdf.rect(x - cubuk_w / 2, alan_y, cubuk_w, cubuk_h, fill=1, stroke=0)
                pdf.setFillColor(cls.METIN)
                pdf.setFont("RaporKalin", 7)
                pdf.drawCentredString(
                    x,
                    min(alan_y + alan_h - 8, alan_y + cubuk_h + 6),
                    str(deger)
                )
                pdf.setFillColor(cls.IKINCIL_METIN)
                pdf.setFont("RaporNormal", 7)
                pdf.drawCentredString(x, alan_y - 14, str(satir[0])[:5])

        pdf.setFillColor(cls.IKINCIL_METIN)
        pdf.setFont("RaporNormal", 7.5)
        pdf.drawString(kenar, 31, "Kaynak: Akıllı Feribot Geçiş Sistemi veritabanı")
        pdf.drawRightString(
            genislik - kenar,
            31,
            f"Oluşturulma: {datetime.now():%d.%m.%Y %H:%M}"
        )
        pdf.showPage()
        pdf.save()
        return dosya_yolu
