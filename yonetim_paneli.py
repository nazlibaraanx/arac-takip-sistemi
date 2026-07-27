import calendar
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from ayarlar import RAPOR_KLASORU
from kamera_kaynagi import (
    kamera_ayarini_kaydet,
    kamera_ayarini_yukle,
)
from pdf_rapor import PdfRapor
from sefer_yonu import (
    SEFER_YONLERI,
    dosya_etiketi,
    sefer_yonunu_oku,
    sefer_yonunu_yaz,
    ters_sefer_yonu,
)
from veritabani import Veritabani
from yukleme_durumu import yukleme_bilgisini_oku, yukleme_durumunu_yaz


class TakvimSecici(tk.Frame):

    AY_ADLARI = (
        "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
    )
    GUNLER = ("Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz")

    def __init__(self, parent, tarih, aralik_modu=False, bitis_tarihi=None):
        super().__init__(
            parent,
            bg="white",
            highlightthickness=1,
            highlightbackground="#E2E8F0",
            padx=10,
            pady=8
        )
        self.aralik_modu = aralik_modu
        self.secili_tarih = tarih.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.bitis_tarihi = (
            bitis_tarihi.replace(hour=0, minute=0, second=0, microsecond=0)
            if bitis_tarihi is not None
            else None
        )
        self.ilk_secim_bekleniyor = aralik_modu and bitis_tarihi is None
        self.gosterilen_yil = tarih.year
        self.gosterilen_ay = tarih.month
        self.takvimi_ciz()

    def onceki_ay(self):
        if self.gosterilen_ay == 1:
            self.gosterilen_yil -= 1
            self.gosterilen_ay = 12
        else:
            self.gosterilen_ay -= 1
        self.takvimi_ciz()

    def sonraki_ay(self):
        if self.gosterilen_ay == 12:
            self.gosterilen_yil += 1
            self.gosterilen_ay = 1
        else:
            self.gosterilen_ay += 1
        self.takvimi_ciz()

    def gun_sec(self, gun):
        yeni_tarih = datetime(
            self.gosterilen_yil,
            self.gosterilen_ay,
            gun
        )
        if not self.aralik_modu:
            self.secili_tarih = yeni_tarih
        elif self.ilk_secim_bekleniyor:
            self.secili_tarih = yeni_tarih
            self.bitis_tarihi = None
            self.ilk_secim_bekleniyor = False
        elif self.bitis_tarihi is not None:
            self.secili_tarih = yeni_tarih
            self.bitis_tarihi = None
        elif yeni_tarih < self.secili_tarih:
            self.bitis_tarihi = self.secili_tarih
            self.secili_tarih = yeni_tarih
        else:
            self.bitis_tarihi = yeni_tarih
        self.takvimi_ciz()

    def degeri_ayarla(self, tarih, bitis_tarihi=None):
        self.secili_tarih = tarih.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.bitis_tarihi = (
            bitis_tarihi.replace(hour=0, minute=0, second=0, microsecond=0)
            if bitis_tarihi is not None
            else None
        )
        self.ilk_secim_bekleniyor = self.aralik_modu and bitis_tarihi is None
        self.gosterilen_yil = tarih.year
        self.gosterilen_ay = tarih.month
        self.takvimi_ciz()

    def degeri_getir(self):
        if self.aralik_modu:
            return self.secili_tarih, self.bitis_tarihi
        return self.secili_tarih

    def takvimi_ciz(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Button(
            self,
            text="‹",
            command=self.onceki_ay,
            relief="flat",
            bg="white",
            fg="#526777",
            activebackground="#F1F7F3",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=3, pady=5)
        tk.Label(
            self,
            text=f"{self.AY_ADLARI[self.gosterilen_ay]} {self.gosterilen_yil}",
            bg="white",
            fg="#344B5A",
            font=("Segoe UI Semibold", 10)
        ).grid(row=0, column=1, columnspan=5, pady=5)
        tk.Button(
            self,
            text="›",
            command=self.sonraki_ay,
            relief="flat",
            bg="white",
            fg="#526777",
            activebackground="#F1F7F3",
            font=("Segoe UI", 12)
        ).grid(row=0, column=6, padx=3, pady=5)

        for sutun, gun_adi in enumerate(self.GUNLER):
            tk.Label(
                self,
                text=gun_adi,
                width=4,
                bg="white",
                fg="#8A9AA6",
                font=("Segoe UI Semibold", 8)
            ).grid(row=1, column=sutun, padx=1, pady=(3, 5))

        ay_satirlari = calendar.monthcalendar(
            self.gosterilen_yil,
            self.gosterilen_ay
        )
        for satir, hafta in enumerate(ay_satirlari, start=2):
            for sutun, gun in enumerate(hafta):
                if gun == 0:
                    tk.Canvas(
                        self,
                        width=34,
                        height=30,
                        bg="white",
                        highlightthickness=0
                    ).grid(row=satir, column=sutun)
                    continue
                hucre_tarihi = datetime(
                    self.gosterilen_yil,
                    self.gosterilen_ay,
                    gun
                )
                secili = (
                    not self.ilk_secim_bekleniyor
                    and self.secili_tarih.year == self.gosterilen_yil
                    and self.secili_tarih.month == self.gosterilen_ay
                    and self.secili_tarih.day == gun
                ) or self.bitis_tarihi == hucre_tarihi
                aralikta = (
                    self.aralik_modu
                    and self.bitis_tarihi is not None
                    and self.secili_tarih < hucre_tarihi < self.bitis_tarihi
                )
                bugun = datetime.now().date() == hucre_tarihi.date()
                gun_alani = tk.Canvas(
                    self,
                    width=34,
                    height=30,
                    bg="white",
                    highlightthickness=0,
                    cursor="hand2"
                )
                gun_alani.grid(row=satir, column=sutun)
                if aralikta:
                    gun_alani.create_rectangle(
                        0,
                        8,
                        34,
                        22,
                        fill="#DDF7E9",
                        outline=""
                    )
                if secili or bugun:
                    gun_alani.create_oval(
                        4,
                        2,
                        30,
                        28,
                        fill="#16A66A" if secili else "#2DBE7F",
                        outline=""
                    )
                gun_alani.create_text(
                    17,
                    15,
                    text=str(gun),
                    font=("Segoe UI", 9),
                    fill="white" if secili or bugun else "#455A68"
                )
                gun_alani.bind(
                    "<Button-1>",
                    lambda _event, deger=gun: self.gun_sec(deger)
                )


class YonetimPaneli:

    ARKA_PLAN = "#F6F8FB"
    KART_RENGI = "#FFFFFF"
    ANA_RENK = "#2563A6"
    ANA_RENK_KOYU = "#1D4F84"
    BASLIK_RENGI = "#18324A"
    METIN_RENGI = "#334155"
    IKINCIL_METIN = "#64748B"
    SINIR_RENGI = "#DCE3EC"
    PASIF_RENK = "#E9EEF5"

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

    GRAFIK_RENKLERI = [
        "#2F75B5",
        "#70AD47",
        "#ED7D31",
        "#A5A5A5",
        "#5B9BD5",
        "#FFC000",
        "#8064A2",
        "#4BACC6"
    ]

    def __init__(self):
        self.vt = Veritabani()
        self.grafik_gunluk_verileri = []
        self.grafik_tur_verileri = []
        self.grafik_aralik_gunluk_verileri = []
        self.grafik_yon_karsilastirmasi = {}
        self.grafik_kapsam_turu = "genel"
        self.grafik_modu = "arac"
        self.grafik_secim_butonlari = {}
        self.grafik_kapsam_haritasi = {}
        self.grafik_donem_haritasi = {}
        self.grafik_rapor_etiketi = "Aylık Genel · İki Yön"
        bugun = datetime.now()
        self.grafik_tarih_baslangic = bugun.replace(day=1)
        self.grafik_tarih_bitis = bugun
        self.grafik_tarih_secildi = False

        self.pencere = tk.Tk()
        self.pencere.title("Akıllı Feribot Yönetim Paneli")
        self.pencere.geometry("1180x720")
        self.pencere.minsize(920, 620)
        self.pencere.protocol("WM_DELETE_WINDOW", self.programi_kapat)
        self.temayi_uygula()

        self.notebook = ttk.Notebook(self.pencere)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.kayitlar_sekmesi = tk.Frame(
            self.notebook, bg=self.ARKA_PLAN
        )
        self.grafik_sekmesi = tk.Frame(
            self.notebook, bg=self.ARKA_PLAN
        )
        self.notebook.add(self.kayitlar_sekmesi, text="Geçiş Kayıtları")
        self.notebook.add(self.grafik_sekmesi, text="Grafikli Rapor")
        self.notebook.bind("<<NotebookTabChanged>>", self.sekme_degisti)

        self.kayitlar_arayuzunu_olustur()
        self.grafik_arayuzunu_olustur()

        ilk_aralik = self.vt.tarih_araligi_grafik_ozeti_getir(
            self.grafik_tarih_baslangic,
            self.grafik_tarih_bitis,
            self.aktif_sefer_yonu
        )
        self.tarih_araligi_sayfasini_goster(
            self.grafik_tarih_baslangic,
            self.grafik_tarih_bitis,
            ilk_aralik["gunluk_ozetler"]
        )
        bugunun_ozeti = self.vt.tarih_araligi_grafik_ozeti_getir(
            bugun,
            bugun,
            self.aktif_sefer_yonu
        )
        bu_ayin_ozeti = self.vt.aylik_grafik_ozeti_getir(
            bugun.year,
            bugun.month,
            self.aktif_sefer_yonu
        )
        self.gunluk_detay_sayfasini_goster(
            bugun,
            bugunun_ozeti["gunluk_ozetler"],
            bu_ayin_ozeti["arac_turleri"]
        )
        self.notebook.select(self.kayitlar_sekmesi)

        self.verileri_yukle()
        self.grafikli_raporu_yenile()
        self.pencere.after(2000, self.otomatik_yenile)
        self.pencere.mainloop()

    def temayi_uygula(self):
        self.pencere.configure(bg=self.ARKA_PLAN)
        self.pencere.option_add("*Font", "{Segoe UI} 10")
        self.pencere.option_add("*Button.Relief", "flat")
        self.pencere.option_add("*Button.BorderWidth", 0)
        self.pencere.option_add("*Button.Cursor", "hand2")
        self.pencere.option_add("*Entry.Relief", "solid")
        self.pencere.option_add("*Entry.BorderWidth", 1)

        stil = ttk.Style(self.pencere)
        try:
            stil.theme_use("clam")
        except tk.TclError:
            pass

        stil.configure(
            "TNotebook",
            background=self.ARKA_PLAN,
            borderwidth=0,
            tabmargins=(8, 8, 0, 0)
        )
        stil.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10),
            padding=(18, 9),
            background=self.PASIF_RENK,
            foreground=self.METIN_RENGI,
            borderwidth=0
        )
        stil.map(
            "TNotebook.Tab",
            background=[("selected", self.KART_RENGI)],
            foreground=[("selected", self.ANA_RENK_KOYU)]
        )
        stil.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=32,
            background=self.KART_RENGI,
            fieldbackground=self.KART_RENGI,
            foreground=self.METIN_RENGI,
            borderwidth=0
        )
        stil.configure(
            "Treeview.Heading",
            font=("Segoe UI Semibold", 10),
            background="#EAF0F7",
            foreground=self.BASLIK_RENGI,
            relief="flat",
            padding=(8, 9)
        )
        stil.map(
            "Treeview",
            background=[("selected", "#D9EAF7")],
            foreground=[("selected", self.BASLIK_RENGI)]
        )
        stil.configure(
            "TCombobox",
            font=("Segoe UI", 10),
            padding=5
        )

    def kayitlar_arayuzunu_olustur(self):
        tk.Label(
            self.kayitlar_sekmesi,
            text="AKILLI FERİBOT YÖNETİM PANELİ",
            font=("Segoe UI Semibold", 19),
            bg=self.ARKA_PLAN,
            fg=self.BASLIK_RENGI
        ).pack(pady=(22, 14))

        self.kamera_ayari_arayuzunu_olustur()

        tk.Label(
            self.kayitlar_sekmesi,
            text="BUGÜNÜN ÖZETİ",
            font=("Segoe UI Semibold", 11),
            bg=self.ARKA_PLAN,
            fg=self.BASLIK_RENGI,
        ).pack(anchor="w", padx=25, pady=(5, 4))

        bilgi_frame = tk.Frame(self.kayitlar_sekmesi, bg=self.ARKA_PLAN)
        bilgi_frame.pack(fill="x", padx=20, pady=(0, 5))
        for sutun in range(5):
            bilgi_frame.grid_columnconfigure(sutun, weight=1)

        self.lbl_toplam = self.ozet_karti_olustur(
            bilgi_frame, 0, "Bugünkü Araç", "0"
        )
        self.lbl_yaya = self.ozet_karti_olustur(
            bilgi_frame, 1, "Bugünkü Yaya", "0"
        )
        self.lbl_gelir = self.ozet_karti_olustur(
            bilgi_frame, 2, "Bugünkü Hasılat", "0,00 TL"
        )
        self.lbl_son_plaka = self.ozet_karti_olustur(
            bilgi_frame, 3, "Son Algılanan Plaka", "Kayıt yok"
        )
        self.lbl_aktif_yon = self.ozet_karti_olustur(
            bilgi_frame, 4, "Aktif Sefer Yönü", "-"
        )

        arama_frame = tk.Frame(self.kayitlar_sekmesi, bg=self.ARKA_PLAN)
        arama_frame.pack(pady=15)

        tk.Label(
            arama_frame,
            text="Plaka Ara:",
            font=("Segoe UI Semibold", 10),
            bg=self.ARKA_PLAN,
            fg=self.METIN_RENGI
        ).pack(side="left", padx=5)

        self.plaka_entry = tk.Entry(
            arama_frame,
            width=23,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.plaka_entry.pack(side="left", padx=5)
        self.plaka_entry.bind("<Return>", lambda event: self.plaka_ara())

        self.buton_olustur(arama_frame, "Ara", self.plaka_ara, 10)
        self.buton_olustur(
            arama_frame,
            "Tümünü Göster",
            self.verileri_yukle,
            15
        )
        self.buton_olustur(
            arama_frame,
            "Rapor Klasörünü Aç",
            self.rapor_klasorunu_ac,
            18
        )
        self.buton_olustur(arama_frame, "Yenile", self.verileri_yukle, 10)
        self.buton_olustur(
            arama_frame,
            "Ücret Yönetimi",
            self.ucret_penceresi,
            16
        )

        tablo_frame = tk.Frame(
            self.kayitlar_sekmesi,
            bg=self.KART_RENGI,
            highlightthickness=1,
            highlightbackground=self.SINIR_RENGI
        )
        tablo_frame.pack(fill="both", expand=True, padx=20, pady=10)

        kolonlar = ("ID", "Tarih", "Saat", "Plaka", "Araç", "Ücret")
        self.tablo = ttk.Treeview(
            tablo_frame,
            columns=kolonlar,
            show="headings",
            height=20
        )

        basliklar = {
            "ID": "ID",
            "Tarih": "Tarih",
            "Saat": "Saat",
            "Plaka": "Plaka",
            "Araç": "Araç Türü",
            "Ücret": "Ücret (TL)"
        }
        genislikler = {
            "ID": 70,
            "Tarih": 140,
            "Saat": 120,
            "Plaka": 200,
            "Araç": 180,
            "Ücret": 140
        }

        for kolon in kolonlar:
            self.tablo.heading(kolon, text=basliklar[kolon])
            self.tablo.column(
                kolon,
                width=genislikler[kolon],
                anchor="center",
                stretch=True
            )

        dikey_scroll = ttk.Scrollbar(
            tablo_frame,
            orient="vertical",
            command=self.tablo.yview
        )
        self.tablo.configure(yscrollcommand=dikey_scroll.set)
        self.tablo.pack(side="left", fill="both", expand=True)
        dikey_scroll.pack(side="right", fill="y")

    def kamera_ayari_arayuzunu_olustur(self):
        ayar = kamera_ayarini_yukle()
        tur_adlari = {
            "video": "Kayıtlı Video",
            "usb": "Yerel / USB Kamera",
        }
        self.kamera_tur_kodlari = {ad: kod for kod, ad in tur_adlari.items()}

        alan = tk.Frame(
            self.kayitlar_sekmesi,
            bg=self.KART_RENGI,
            highlightthickness=1,
            highlightbackground=self.SINIR_RENGI,
            padx=12,
            pady=8,
        )
        alan.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(
            alan,
            text="Görüntü Kaynağı",
            font=("Segoe UI Semibold", 10),
            bg=self.KART_RENGI,
            fg=self.BASLIK_RENGI,
        ).pack(side="left", padx=(0, 10))

        self.kamera_tur_var = tk.StringVar(value=tur_adlari[ayar["tur"]])
        self.kamera_tur_secimi = ttk.Combobox(
            alan,
            textvariable=self.kamera_tur_var,
            values=list(tur_adlari.values()),
            state="readonly",
            width=16,
        )
        self.kamera_tur_secimi.pack(side="left", padx=(0, 8))
        self.kamera_tur_secimi.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.kamera_alani_guncelle(),
        )

        self.kamera_deger_var = tk.StringVar(value=str(ayar["deger"]))
        self.kamera_deger_entry = tk.Entry(
            alan,
            textvariable=self.kamera_deger_var,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1,
        )
        self.kamera_deger_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 8), ipady=5
        )

        self.kamera_gozat_butonu = tk.Button(
            alan,
            text="Gözat",
            command=self.kamera_video_sec,
            font=("Segoe UI", 9),
            bg="#E9EEF5",
            fg="#334155",
            relief="flat",
            cursor="hand2",
        )
        self.kamera_gozat_butonu.pack(side="left", padx=4, ipadx=9, ipady=4)

        tk.Button(
            alan,
            text="Kaydet",
            command=self.kamera_ayarini_kaydet,
            font=("Segoe UI Semibold", 9),
            bg=self.ANA_RENK,
            fg="white",
            activebackground=self.ANA_RENK_KOYU,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(4, 0), ipadx=11, ipady=4)

        yukleme_bilgisi = yukleme_bilgisini_oku(
            varsayilan=False
        )
        self.yukleme_aktif = yukleme_bilgisi["aktif"]
        self.aktif_sefer_id = yukleme_bilgisi["sefer_id"]
        self.yukleme_butonu = tk.Button(
            alan,
            command=self.yukleme_durumunu_degistir,
            font=("Segoe UI Semibold", 9),
            relief="flat",
            cursor="hand2",
        )
        self.yukleme_butonu.pack(
            side="left", padx=(12, 0), ipadx=11, ipady=4
        )
        self.yukleme_butonunu_guncelle()
        self.kamera_alani_guncelle(degeri_degistir=False)

        sefer_alani = tk.Frame(
            self.kayitlar_sekmesi,
            bg=self.KART_RENGI,
            highlightthickness=1,
            highlightbackground=self.SINIR_RENGI,
            padx=12,
            pady=7,
        )
        sefer_alani.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(
            sefer_alani,
            text="Sefer Yönü",
            font=("Segoe UI Semibold", 10),
            bg=self.KART_RENGI,
            fg=self.BASLIK_RENGI,
        ).pack(side="left", padx=(0, 10))
        self.aktif_sefer_yonu = sefer_yonunu_oku()
        if self.yukleme_aktif and self.aktif_sefer_id is None:
            self.aktif_sefer_id = self.vt.sefer_baslat(
                self.aktif_sefer_yonu
            )
            yukleme_durumunu_yaz(
                True, sefer_id=self.aktif_sefer_id
            )
        self.sefer_yonu_var = tk.StringVar(value=self.aktif_sefer_yonu)
        self.sefer_yonu_secimi = ttk.Combobox(
            sefer_alani,
            textvariable=self.sefer_yonu_var,
            values=SEFER_YONLERI,
            state="readonly",
            width=22,
        )
        self.sefer_yonu_secimi.pack(side="left")
        self.sefer_yonu_secimi.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.sefer_yonu_degisti(),
        )
        self.sefer_yonu_durum_label = tk.Label(
            sefer_alani,
            text="Bu yüklemenin kayıtları seçilen yöne yazılır.",
            font=("Segoe UI", 9),
            bg=self.KART_RENGI,
            fg=self.IKINCIL_METIN,
        )
        self.sefer_yonu_durum_label.pack(side="left", padx=(14, 0))

    def sefer_yonu_degisti(self):
        if self.yukleme_aktif:
            self.sefer_yonu_var.set(self.aktif_sefer_yonu)
            return
        self.aktif_sefer_yonu = sefer_yonunu_yaz(
            self.sefer_yonu_var.get()
        )
        self.verileri_yukle()
        self.grafikli_raporu_yenile(hata_goster=False)
        if hasattr(self, "gunluk_detay_tarih"):
            self.gunluk_detay_tarih_listesini_guncelle(
                self.gunluk_detay_tarih
            )

    def kamera_alani_guncelle(self, degeri_degistir=True):
        tur = self.kamera_tur_kodlari[self.kamera_tur_var.get()]
        self.kamera_gozat_butonu.config(
            state="normal" if tur == "video" else "disabled"
        )
        if not degeri_degistir:
            return
        varsayilanlar = {
            "video": os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "videolar",
                "kayit.mp4",
            ),
            "usb": "0",
        }
        self.kamera_deger_var.set(varsayilanlar[tur])

    def kamera_video_sec(self):
        dosya_yolu = filedialog.askopenfilename(
            parent=self.pencere,
            title="Kayıtlı Video Seç",
            filetypes=[
                ("Video Dosyaları", "*.mp4 *.avi *.mov *.mkv"),
                ("Tüm Dosyalar", "*.*"),
            ],
        )
        if dosya_yolu:
            self.kamera_deger_var.set(dosya_yolu)

    def kamera_ayarini_kaydet(self):
        tur = self.kamera_tur_kodlari[self.kamera_tur_var.get()]
        deger = self.kamera_deger_var.get().strip()
        try:
            if tur == "video" and not os.path.isfile(deger):
                raise ValueError(
                    "Seçilen video dosyası bulunamadı. "
                    "Gözat ile geçerli bir video seçin."
                )
            ayar = kamera_ayarini_kaydet({"tur": tur, "deger": deger})
            self.kamera_deger_var.set(str(ayar["deger"]))
            if tur == "usb":
                if self.yukleme_aktif:
                    self.vt.sefer_bitir(self.aktif_sefer_id)
                self.yukleme_aktif = False
                self.aktif_sefer_id = None
                yukleme_durumunu_yaz(False, sefer_id=None)
                self.yukleme_butonunu_guncelle()
            messagebox.showinfo(
                "Kamera Ayarı Kaydedildi",
                "Yeni görüntü kaynağı kaydedildi.\n\n"
                "Ana geçiş sistemi açıksa kapatıp yeniden başlatın.",
            )
        except ValueError as hata:
            messagebox.showerror("Geçersiz Kamera Ayarı", str(hata))

    def yukleme_durumunu_degistir(self):
        if not self.yukleme_aktif:
            self.aktif_sefer_yonu = sefer_yonunu_yaz(
                self.sefer_yonu_var.get()
            )
            self.aktif_sefer_id = self.vt.sefer_baslat(
                self.aktif_sefer_yonu
            )
            self.yukleme_aktif = True
        else:
            self.vt.sefer_bitir(self.aktif_sefer_id)
            self.aktif_sefer_id = None
            self.yukleme_aktif = False
            self.aktif_sefer_yonu = sefer_yonunu_yaz(
                ters_sefer_yonu(self.aktif_sefer_yonu)
            )
            self.sefer_yonu_var.set(self.aktif_sefer_yonu)
            self.sefer_yonu_durum_label.config(
                text=(
                    "Sonraki sefer yönü otomatik hazırlandı: "
                    f"{self.aktif_sefer_yonu}"
                )
            )
            self.verileri_yukle()
            self.grafik_kapsamlarini_guncelle()
            self.grafikli_raporu_yenile(hata_goster=False)
        yukleme_durumunu_yaz(
            self.yukleme_aktif,
            sefer_id=self.aktif_sefer_id,
        )
        self.yukleme_butonunu_guncelle()

    def yukleme_butonunu_guncelle(self):
        if hasattr(self, "sefer_yonu_secimi"):
            self.sefer_yonu_secimi.config(
                state="disabled" if self.yukleme_aktif else "readonly"
            )
        if self.yukleme_aktif:
            self.yukleme_butonu.config(
                text="Yüklemeyi Bitir",
                bg="#FDECEC",
                fg="#A33A3A",
                activebackground="#F8D7D7",
            )
        else:
            self.yukleme_butonu.config(
                text="Yüklemeyi Başlat",
                bg="#DDF4E8",
                fg="#147A4B",
                activebackground="#CBEAD9",
            )

    @staticmethod
    def buton_olustur(parent, metin, komut, genislik):
        tk.Button(
            parent,
            text=metin,
            command=komut,
            width=genislik,
            font=("Segoe UI", 9),
            bg="#E9EEF5",
            fg="#334155",
            activebackground="#DCE6F1",
            activeforeground="#18324A",
            relief="flat",
            bd=0,
            cursor="hand2"
        ).pack(side="left", padx=4, ipady=4)

    def takvim_filtresi_olustur(self, parent):
        alan = tk.Frame(parent, bg=self.ARKA_PLAN)
        alan.pack(side="left", padx=(24, 0))
        simge = tk.Canvas(
            alan, width=24, height=24, bg=self.ARKA_PLAN,
            highlightthickness=0, cursor="hand2"
        )
        simge.pack(side="left", padx=(0, 5))
        simge.create_rectangle(3, 5, 21, 21, outline="#16A66A", width=1)
        simge.create_line(3, 10, 21, 10, fill="#16A66A")
        simge.create_line(8, 3, 8, 7, fill="#16A66A", width=2)
        simge.create_line(16, 3, 16, 7, fill="#16A66A", width=2)
        for x, y, gun in (
            (7, 13, "1"), (12, 13, "2"), (17, 13, "3"),
            (7, 18, "4"), (12, 18, "5"), (17, 18, "6")
        ):
            simge.create_text(
                x, y, text=gun, fill="#16A66A", font=("Segoe UI", 5)
            )
        simge.bind("<Button-1>", lambda _event: self.tarih_araligi_penceresi())
        self.grafik_tarih_araligi_butonu = tk.Button(
            alan,
            text=(
                f"{self.grafik_tarih_baslangic:%d.%m.%Y}  –  "
                f"{self.grafik_tarih_bitis:%d.%m.%Y}"
            ),
            command=self.tarih_araligi_penceresi,
            width=19,
            font=("Segoe UI", 8),
            bg="#FBFCFE",
            fg=self.METIN_RENGI,
            relief="solid",
            bd=1,
            activebackground="#F1F5F9",
            highlightthickness=0
        )
        self.grafik_tarih_araligi_butonu.pack(side="left", ipady=2)

    def grafik_arayuzunu_olustur(self):
        ust_frame = tk.Frame(self.grafik_sekmesi, bg=self.ARKA_PLAN)
        ust_frame.pack(fill="x", padx=24, pady=(16, 9))

        self.grafik_sayfa_basligi = tk.Label(
            ust_frame,
            text="Aylık Grafik Raporu",
            font=("Segoe UI Semibold", 16),
            bg=self.ARKA_PLAN,
            fg=self.BASLIK_RENGI
        )
        self.grafik_sayfa_basligi.pack(side="left")

        aksiyon_frame = tk.Frame(ust_frame, bg=self.ARKA_PLAN)
        aksiyon_frame.pack(side="right")
        tk.Button(
            aksiyon_frame,
            text="Yenile",
            command=self.grafikli_raporu_yenile,
            width=8,
            font=("Segoe UI", 8),
            bg=self.ARKA_PLAN,
            fg=self.IKINCIL_METIN,
            relief="flat"
        ).pack(side="left", padx=(0, 5), ipady=2)
        tk.Button(
            aksiyon_frame,
            text="PDF'ye Aktar",
            command=self.grafikli_raporu_pdf_kaydet,
            width=12,
            font=("Segoe UI", 8),
            bg="#FBFCFE",
            fg=self.METIN_RENGI,
            relief="solid",
            bd=1,
            activebackground="#EEF3F6"
        ).pack(side="left", ipady=2)

        kartlar = tk.Frame(self.grafik_sekmesi, bg=self.ARKA_PLAN)
        kartlar.pack(fill="x", padx=24, pady=(5, 8))
        for sutun in range(4):
            kartlar.grid_columnconfigure(sutun, weight=1)

        self.grafik_lbl_toplam_arac = self.ozet_karti_olustur(
            kartlar,
            0,
            "Aylık Toplam Araç",
            "0"
        )
        self.grafik_lbl_hasilat = self.ozet_karti_olustur(
            kartlar,
            2,
            "Aylık Toplam Hasılat",
            "0,00 TL"
        )
        self.grafik_lbl_yaya = self.ozet_karti_olustur(
            kartlar,
            1,
            "Aylık Yaya Yolcu",
            "0"
        )
        self.grafik_lbl_yogun_gun = self.ozet_karti_olustur(
            kartlar,
            3,
            "Ayın En Yoğun Günü",
            "Kayıt yok"
        )

        self.yon_karsilastirma_frame = tk.Frame(
            self.grafik_sekmesi, bg=self.ARKA_PLAN
        )
        self.yon_karsilastirma_frame.pack(fill="x", padx=24, pady=(0, 5))
        for sutun in range(2):
            self.yon_karsilastirma_frame.grid_columnconfigure(sutun, weight=1)

        self.yon_karsilastirma_etiketleri = {}
        yon_renkleri = ("#2F75B5", "#ED7D31")
        for sutun, (yon, renk) in enumerate(zip(SEFER_YONLERI, yon_renkleri)):
            kart = tk.Frame(
                self.yon_karsilastirma_frame,
                bg=self.KART_RENGI,
                highlightthickness=1,
                highlightbackground=renk,
                padx=14,
                pady=7,
            )
            kart.grid(
                row=0, column=sutun, sticky="ew", padx=5
            )
            tk.Label(
                kart,
                text=yon.replace(" - ", " → "),
                font=("Segoe UI Semibold", 10),
                bg=self.KART_RENGI,
                fg=renk,
            ).pack(anchor="w")
            deger = tk.Label(
                kart,
                text="0 araç  ·  0 yaya  ·  0,00 TL",
                font=("Segoe UI", 10),
                bg=self.KART_RENGI,
                fg=self.METIN_RENGI,
            )
            deger.pack(anchor="w", pady=(4, 0))
            self.yon_karsilastirma_etiketleri[yon] = deger

        grafik_secimi = tk.Frame(self.grafik_sekmesi, bg=self.ARKA_PLAN)
        self.grafik_secim_frame = grafik_secimi
        grafik_secimi.pack(fill="x", padx=24, pady=(7, 0))
        tk.Label(
            grafik_secimi,
            text="Grafik:",
            font=("Segoe UI", 9),
            bg=self.ARKA_PLAN,
            fg=self.METIN_RENGI
        ).pack(side="left", padx=(0, 8))

        for mod, metin in (("arac", "Araç"), ("yaya", "Yaya Yolcu")):
            buton = tk.Button(
                grafik_secimi,
                text=metin,
                command=lambda secim=mod: self.grafik_modunu_degistir(secim),
                width=11,
                font=("Segoe UI", 8),
                relief="flat",
                cursor="hand2"
            )
            buton.pack(side="left", padx=(0, 3), ipady=3)
            self.grafik_secim_butonlari[mod] = buton

        tk.Label(
            grafik_secimi,
            text="Rapor Kapsamı:",
            font=("Segoe UI", 9),
            bg=self.ARKA_PLAN,
            fg=self.METIN_RENGI
        ).pack(side="left", padx=(22, 8))
        self.grafik_kapsam_var = tk.StringVar()
        self.grafik_kapsam_secimi = ttk.Combobox(
            grafik_secimi,
            textvariable=self.grafik_kapsam_var,
            state="readonly",
            width=42,
        )
        self.grafik_kapsam_secimi.pack(side="left")
        self.grafik_kapsam_secimi.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.grafikli_raporu_yenile(),
        )
        self.grafik_kapsamlarini_guncelle()

        tk.Label(
            grafik_secimi,
            text="Dönem:",
            font=("Segoe UI", 9),
            bg=self.ARKA_PLAN,
            fg=self.METIN_RENGI
        ).pack(side="left", padx=(16, 8))
        self.grafik_donem_var = tk.StringVar()
        self.grafik_donem_secimi = ttk.Combobox(
            grafik_secimi,
            textvariable=self.grafik_donem_var,
            state="readonly",
            width=15,
        )
        self.grafik_donem_secimi.pack(side="left")
        self.grafik_donem_secimi.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.grafikli_raporu_yenile(),
        )
        self.grafik_donemlerini_guncelle()

        grafikler = tk.Frame(self.grafik_sekmesi, bg=self.ARKA_PLAN)
        grafikler.pack(fill="both", expand=True, padx=24, pady=(9, 18))
        grafikler.grid_columnconfigure(0, weight=3)
        grafikler.grid_columnconfigure(1, weight=2)
        grafikler.grid_rowconfigure(0, weight=1)

        self.gunluk_canvas = tk.Canvas(
            grafikler,
            bg="white",
            highlightthickness=1,
            highlightbackground="#E5EAF0"
        )
        self.gunluk_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )
        self.gunluk_canvas.bind(
            "<Configure>",
            lambda event: self.gunluk_grafigi_ciz()
        )

        self.tur_canvas = tk.Canvas(
            grafikler,
            bg="white",
            highlightthickness=1,
            highlightbackground="#E5EAF0"
        )
        self.tur_canvas.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )
        self.tur_canvas.bind(
            "<Configure>",
            lambda event: self.tur_grafigi_ciz()
        )

        self.aralik_grafik_frame = tk.Frame(
            self.grafik_sekmesi,
            bg=self.KART_RENGI,
            highlightthickness=1,
            highlightbackground="#E5EAF0"
        )
        aralik_baslik = tk.Frame(
            self.aralik_grafik_frame, bg=self.KART_RENGI
        )
        aralik_baslik.pack(fill="x", padx=18, pady=(10, 2))
        tk.Label(
            aralik_baslik,
            text="Seçilen Tarih Aralığı Performans Analizi",
            font=("Segoe UI Semibold", 10),
            bg=self.KART_RENGI,
            fg=self.BASLIK_RENGI
        ).pack(side="left")
        self.aralik_grafik_aciklama = tk.Label(
            aralik_baslik,
            text="",
            font=("Segoe UI", 8),
            bg=self.KART_RENGI,
            fg=self.IKINCIL_METIN
        )
        self.aralik_grafik_aciklama.pack(side="right")
        self.aralik_canvas = tk.Canvas(
            self.aralik_grafik_frame,
            height=145,
            bg="white",
            highlightthickness=0
        )
        self.aralik_canvas.pack(fill="x", padx=12, pady=(0, 8))
        self.aralik_canvas.bind(
            "<Configure>", lambda _event: self.tarih_araligi_grafigi_ciz()
        )
        self.grafik_secim_butonlarini_guncelle()

    def grafik_kapsamlarini_guncelle(self):
        secenekler = [
            "Aylık Genel · İki Yön",
            "Aylık · Malatya - Baskil",
            "Aylık · Baskil - Malatya",
        ]
        self.grafik_kapsam_haritasi = {
            secenekler[0]: ("genel", None),
            secenekler[1]: ("yon", "Malatya - Baskil"),
            secenekler[2]: ("yon", "Baskil - Malatya"),
        }
        mevcut = self.grafik_kapsam_var.get()
        self.grafik_kapsam_secimi["values"] = secenekler
        self.grafik_kapsam_var.set(
            mevcut if mevcut in secenekler else secenekler[0]
        )

    def grafik_donemlerini_guncelle(self):
        bugun = datetime.now()
        donemler = self.vt.tum_rapor_aylarini_getir()
        if (bugun.year, bugun.month) not in donemler:
            donemler.insert(0, (bugun.year, bugun.month))
        self.grafik_donem_haritasi = {
            f"{self.AY_ADLARI[ay]} {yil}": (yil, ay)
            for yil, ay in donemler
        }
        secenekler = list(self.grafik_donem_haritasi)
        mevcut = self.grafik_donem_var.get()
        self.grafik_donem_secimi["values"] = secenekler
        self.grafik_donem_var.set(
            mevcut if mevcut in secenekler else secenekler[0]
        )

    def grafik_modunu_degistir(self, mod):
        if mod not in ("arac", "yaya"):
            return

        self.grafik_modu = mod
        self.grafik_secim_butonlarini_guncelle()

        if mod == "yaya":
            self.tur_canvas.grid_remove()
            self.gunluk_canvas.grid_configure(columnspan=2, padx=0)
        else:
            self.gunluk_canvas.grid_configure(columnspan=1, padx=(0, 8))
            self.tur_canvas.grid()

        self.grafik_ozet_kartlarini_guncelle()
        self.gunluk_grafigi_ciz()
        self.tur_grafigi_ciz()
        self.tarih_araligi_grafigi_ciz()

    def grafik_secim_butonlarini_guncelle(self):
        for mod, buton in self.grafik_secim_butonlari.items():
            secili = mod == self.grafik_modu
            buton.config(
                bg=self.ANA_RENK if secili else self.PASIF_RENK,
                fg="white" if secili else self.METIN_RENGI,
                activebackground=(
                    self.ANA_RENK_KOYU if secili else "#DCE4EE"
                ),
                activeforeground="white" if secili else self.METIN_RENGI
            )

    def grafik_ozet_kartlarini_guncelle(self):
        toplam_arac = sum(
            int(satir[1]) for satir in self.grafik_gunluk_verileri
        )
        toplam_yaya = sum(
            int(satir[2]) for satir in self.grafik_gunluk_verileri
        )
        toplam_hasilat = sum(
            float(satir[3]) for satir in self.grafik_gunluk_verileri
        )

        kartlar = (
            self.grafik_lbl_toplam_arac,
            self.grafik_lbl_yaya,
            self.grafik_lbl_hasilat,
            self.grafik_lbl_yogun_gun
        )
        for kart_label in kartlar:
            kart_label.kart.grid_remove()

        if self.grafik_modu == "yaya":
            self.grafik_lbl_yaya.config(
                text=f"{toplam_yaya:,}".replace(",", ".")
            )
            self.grafik_lbl_yaya.kart.grid(
                row=0, column=0, columnspan=2, sticky="ew", padx=5, ipady=8
            )
            veri_indeksi = 2
            birim = "yaya yolcu"
            self.grafik_lbl_yogun_gun.baslik_label.config(
                text="Ayın En Yoğun Yaya Günü"
            )
            self.grafik_lbl_yogun_gun.kart.grid(
                row=0, column=2, columnspan=2, sticky="ew", padx=5, ipady=8
            )
        else:
            self.grafik_lbl_toplam_arac.config(
                text=f"{toplam_arac:,}".replace(",", ".")
            )
            self.grafik_lbl_hasilat.config(
                text=f"{toplam_hasilat:,.2f} TL".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            self.grafik_lbl_toplam_arac.kart.grid(
                row=0, column=0, sticky="ew", padx=5, ipady=8
            )
            self.grafik_lbl_hasilat.kart.grid(
                row=0, column=1, sticky="ew", padx=5, ipady=8
            )
            veri_indeksi = 1
            birim = "araç"
            self.grafik_lbl_yogun_gun.baslik_label.config(
                text="Ayın En Yoğun Araç Günü"
            )
            self.grafik_lbl_yogun_gun.kart.grid(
                row=0, column=2, columnspan=2, sticky="ew", padx=5, ipady=8
            )

        if self.grafik_gunluk_verileri:
            yogun_satir = max(
                self.grafik_gunluk_verileri,
                key=lambda satir: int(satir[veri_indeksi])
            )
            yogun_tarih = str(yogun_satir[0])
            yogun_sayi = int(yogun_satir[veri_indeksi])
            yogun_metin = (
                f"{yogun_tarih} · {yogun_sayi} {birim}"
            )
        else:
            yogun_metin = "Kayıt yok"

        self.grafik_lbl_yogun_gun.config(text=yogun_metin)
        self.yon_karsilastirmasini_guncelle()

    def yon_karsilastirmasini_guncelle(self):
        if self.grafik_kapsam_turu != "genel":
            self.yon_karsilastirma_frame.pack_forget()
            return

        self.yon_karsilastirma_frame.pack(
            fill="x", padx=24, pady=(0, 5), before=self.grafik_secim_frame
        )
        for yon in SEFER_YONLERI:
            ozet = self.grafik_yon_karsilastirmasi.get(yon, {})
            arac = int(ozet.get("toplam_arac", 0))
            yaya = int(ozet.get("toplam_yaya", 0))
            hasilat = float(ozet.get("toplam_hasilat", 0))
            hasilat_metni = (
                f"{hasilat:,.2f}".replace(",", "X")
                .replace(".", ",").replace("X", ".")
            )
            self.yon_karsilastirma_etiketleri[yon].config(
                text=f"{arac} araç  ·  {yaya} yaya  ·  {hasilat_metni} TL"
            )

    def ozet_karti_olustur(self, parent, sutun, baslik, deger):
        kart = tk.Frame(
            parent,
            bg=self.KART_RENGI,
            highlightthickness=1,
            highlightbackground=self.SINIR_RENGI
        )
        kart.grid(
            row=0,
            column=sutun,
            sticky="ew",
            padx=5,
            ipady=8
        )
        baslik_label = tk.Label(
            kart,
            text=baslik,
            font=("Segoe UI", 9),
            bg=self.KART_RENGI,
            fg=self.IKINCIL_METIN
        )
        baslik_label.pack()
        deger_label = tk.Label(
            kart,
            text=deger,
            font=("Segoe UI Semibold", 15),
            bg=self.KART_RENGI,
            fg=self.BASLIK_RENGI
        )
        deger_label.pack(pady=(6, 0))
        deger_label.kart = kart
        deger_label.baslik_label = baslik_label
        return deger_label

    def arac_turunu_turkcelestir(self, arac_turu):
        arac_isimleri = {
            "car": "Otomobil",
            "truck": "Kamyon",
            "bus": "Toplu Taşıma",
            "motorcycle": "Motosiklet",
            "minibus": "Toplu Taşıma",
            "Otobüs": "Toplu Taşıma",
            "Servis": "Toplu Taşıma",
            "Minibüs": "Toplu Taşıma"
        }
        return arac_isimleri.get(arac_turu, arac_turu)

    def tarih_araligi_penceresi(self):
        pencere = tk.Toplevel(self.pencere)
        pencere.title("Tarih Aralığı Seç")
        pencere.geometry("350x400")
        pencere.resizable(False, False)
        pencere.configure(bg="white")
        pencere.transient(self.pencere)
        pencere.grab_set()

        tk.Label(
            pencere,
            text="Grafik Tarih Aralığı",
            font=("Segoe UI Semibold", 13),
            bg="white",
            fg="#344B5A"
        ).pack(pady=(15, 9))

        icerik = tk.Frame(pencere, bg="white")
        icerik.pack(fill="both", expand=True, padx=18)
        takvim_alani = tk.Frame(icerik, bg="white")
        takvim_alani.pack(fill="both", expand=True)

        bugun = datetime.now()
        if self.grafik_tarih_secildi:
            varsayilan_baslangic = self.grafik_tarih_baslangic
            varsayilan_bitis = self.grafik_tarih_bitis
        else:
            varsayilan_baslangic = bugun
            varsayilan_bitis = None
        tk.Label(
            takvim_alani,
            text="Önce başlangıç, sonra bitiş gününe tıklayın",
            font=("Segoe UI", 9),
            bg="white",
            fg="#758793"
        ).pack(pady=(0, 7))
        aralik_takvimi = TakvimSecici(
            takvim_alani,
            varsayilan_baslangic,
            aralik_modu=True,
            bitis_tarihi=varsayilan_bitis
        )
        aralik_takvimi.pack()

        butonlar = tk.Frame(pencere, bg="white")
        butonlar.pack(fill="x", padx=18, pady=(10, 16))
        tk.Button(
            butonlar,
            text="İptal",
            command=pencere.destroy,
            width=11,
            bg="#E9EEF2",
            fg="#526777",
            relief="flat"
        ).pack(side="right", padx=(7, 0))
        tk.Button(
            butonlar,
            text="Uygula",
            command=lambda: self.grafik_tarih_filtresini_uygula(
                aralik_takvimi.degeri_getir(), pencere
            ),
            width=11,
            bg="#16A66A",
            fg="white"
        ).pack(side="right")
    def grafik_tarih_filtresini_uygula(self, tarih_araligi, pencere=None):
        baslangic, bitis = tarih_araligi
        if bitis is None:
            messagebox.showwarning(
                "Eksik Tarih",
                "Takvimden önce başlangıç, sonra bitiş gününü seçin."
            )
            return

        self.grafik_tarih_baslangic = baslangic
        self.grafik_tarih_bitis = bitis
        self.grafik_tarih_secildi = True
        self.grafik_tarih_araligi_butonu.config(
            text=(
                f"{baslangic.strftime('%d.%m.%Y')}  –  "
                f"{bitis.strftime('%d.%m.%Y')}"
            )
        )
        if pencere is not None:
            pencere.destroy()
        ozet = self.vt.tarih_araligi_grafik_ozeti_getir(
            baslangic,
            bitis,
            self.aktif_sefer_yonu
        )
        self.grafik_aralik_gunluk_verileri = ozet["gunluk_ozetler"]
        self.aralik_grafik_aciklama.config(
            text=(
                f"{baslangic.strftime('%d.%m.%Y')} – "
                f"{bitis.strftime('%d.%m.%Y')}"
            )
        )
        self.tarih_araligi_sayfasini_goster(
            baslangic,
            bitis,
            self.grafik_aralik_gunluk_verileri
        )

    def gunluk_detay_sayfasini_goster(self, tarih, gunluk_veriler, tur_verileri):
        if not hasattr(self, "gunluk_detay_sekmesi"):
            self.gunluk_detay_sekmesi = tk.Frame(
                self.notebook, bg=self.ARKA_PLAN
            )
            self.notebook.add(
                self.gunluk_detay_sekmesi, text="Günlük Detaylı Analiz"
            )
            baslik = tk.Frame(self.gunluk_detay_sekmesi, bg=self.ARKA_PLAN)
            baslik.pack(fill="x", padx=26, pady=(20, 12))
            tk.Label(
                baslik,
                text="Günlük Detaylı Geçiş Analizi",
                font=("Segoe UI Semibold", 16),
                bg=self.ARKA_PLAN,
                fg=self.BASLIK_RENGI
            ).pack(side="left")
            tarih_secim_alani = tk.Frame(baslik, bg=self.ARKA_PLAN)
            tarih_secim_alani.pack(side="left", padx=(24, 0))
            tk.Label(
                tarih_secim_alani,
                text="Gün:",
                font=("Segoe UI", 9),
                bg=self.ARKA_PLAN,
                fg=self.IKINCIL_METIN
            ).pack(side="left", padx=(0, 6))
            self.gunluk_detay_tarih_secimi = ttk.Combobox(
                tarih_secim_alani,
                state="readonly",
                width=14,
                font=("Segoe UI", 9)
            )
            self.gunluk_detay_tarih_secimi.pack(side="left")
            self.gunluk_detay_tarih_secimi.bind(
                "<<ComboboxSelected>>",
                lambda _event: self.gunluk_detay_tarihi_degisti()
            )
            self.gunluk_detay_tarih_label = tk.Label(
                baslik, text="", font=("Segoe UI", 9),
                bg=self.ARKA_PLAN, fg=self.IKINCIL_METIN
            )
            self.gunluk_detay_tarih_label.pack(side="right")
            tk.Button(
                baslik,
                text="PDF'ye Aktar",
                command=self.gunluk_detay_pdf_kaydet,
                width=12,
                font=("Segoe UI", 8),
                bg="#FBFCFE",
                fg=self.METIN_RENGI,
                relief="solid",
                bd=1
            ).pack(side="right", padx=(0, 14), ipady=2)

            kartlar = tk.Frame(self.gunluk_detay_sekmesi, bg=self.ARKA_PLAN)
            kartlar.pack(fill="x", padx=26, pady=(0, 10))
            for sutun in range(3):
                kartlar.grid_columnconfigure(sutun, weight=1)
            self.gunluk_detay_arac = self.ozet_karti_olustur(
                kartlar, 0, "Günlük Araç", "0"
            )
            self.gunluk_detay_yaya = self.ozet_karti_olustur(
                kartlar, 1, "Günlük Yaya Yolcu", "0"
            )
            self.gunluk_detay_hasilat = self.ozet_karti_olustur(
                kartlar, 2, "Günlük Hasılat", "0,00 TL"
            )

            grafikler = tk.Frame(self.gunluk_detay_sekmesi, bg=self.ARKA_PLAN)
            grafikler.pack(fill="both", expand=True, padx=26, pady=(0, 24))
            grafikler.grid_columnconfigure(0, weight=3)
            grafikler.grid_columnconfigure(1, weight=2)
            grafikler.grid_rowconfigure(0, weight=1)
            self.gunluk_detay_canvas = tk.Canvas(
                grafikler, bg="white", highlightthickness=1,
                highlightbackground=self.SINIR_RENGI
            )
            self.gunluk_detay_canvas.grid(
                row=0, column=0, sticky="nsew", padx=(0, 7)
            )
            self.gunluk_detay_tur_canvas = tk.Canvas(
                grafikler, bg="white", highlightthickness=1,
                highlightbackground=self.SINIR_RENGI
            )
            self.gunluk_detay_tur_canvas.grid(
                row=0, column=1, sticky="nsew", padx=(7, 0)
            )
            self.gunluk_detay_canvas.bind(
                "<Configure>", lambda _event: self.gunluk_detay_grafigi_ciz()
            )
            self.gunluk_detay_tur_canvas.bind(
                "<Configure>", lambda _event: self.gunluk_detay_tur_grafigi_ciz()
            )

        self.gunluk_detay_tarih = tarih
        self.gunluk_detay_veriler = list(gunluk_veriler)
        self.gunluk_detay_tur_verileri = list(tur_verileri)
        self.gunluk_detay_tarih_label.config(text=f"Rapor tarihi · {tarih:%d.%m.%Y}")
        self.gunluk_detay_tarih_listesini_guncelle(tarih)
        satir = self.gunluk_detay_veriler[0] if self.gunluk_detay_veriler else (
            tarih.strftime("%d.%m.%Y"), 0, 0, 0.0
        )
        self.gunluk_detay_arac.config(text=str(int(satir[1])))
        self.gunluk_detay_yaya.config(text=str(int(satir[2])))
        self.gunluk_detay_hasilat.config(
            text=f"{float(satir[3]):,.2f} TL".replace(",", "X")
            .replace(".", ",").replace("X", ".")
        )
        self.gunluk_detay_grafigi_ciz()
        self.gunluk_detay_tur_grafigi_ciz()
        self.notebook.select(self.gunluk_detay_sekmesi)

    def gunluk_detay_tarih_listesini_guncelle(self, secili_tarih):
        tarihler = [
            str(satir[0])
            for satir in self.vt.gunluk_ozetleri_getir(
                self.aktif_sefer_yonu
            )
        ]
        secili_metin = secili_tarih.strftime("%d.%m.%Y")
        if secili_metin not in tarihler:
            tarihler.append(secili_metin)
        tarihler.sort(
            key=lambda deger: datetime.strptime(deger, "%d.%m.%Y"),
            reverse=True
        )
        self.gunluk_detay_tarih_secimi["values"] = tarihler
        self.gunluk_detay_tarih_secimi.set(secili_metin)

    def gunluk_detay_tarihi_degisti(self):
        tarih_metni = self.gunluk_detay_tarih_secimi.get()
        if not tarih_metni:
            return
        tarih = datetime.strptime(tarih_metni, "%d.%m.%Y")
        gunluk_ozet = self.vt.tarih_araligi_grafik_ozeti_getir(
            tarih, tarih, self.aktif_sefer_yonu
        )
        aylik_ozet = self.vt.aylik_grafik_ozeti_getir(
            tarih.year, tarih.month, self.aktif_sefer_yonu
        )
        self.gunluk_detay_sayfasini_goster(
            tarih,
            gunluk_ozet["gunluk_ozetler"],
            aylik_ozet["arac_turleri"]
        )

    def gunluk_detay_pdf_kaydet(self):
        tarih = self.gunluk_detay_tarih
        dosya_yolu = filedialog.asksaveasfilename(
            parent=self.pencere,
            title="Günlük Detaylı Analizi PDF Olarak Kaydet",
            initialdir=RAPOR_KLASORU,
            initialfile=(
                "Feribot_Gunluk_Detayli_Analiz_"
                f"{dosya_etiketi(self.aktif_sefer_yonu)}_{tarih:%Y%m%d}.pdf"
            ),
            defaultextension=".pdf",
            filetypes=[("PDF Dosyası", "*.pdf")]
        )
        if not dosya_yolu:
            return
        PdfRapor.tarih_araligi_olustur(
            dosya_yolu=dosya_yolu,
            baslangic=tarih,
            bitis=tarih,
            gunluk_ozetler=(
                self.gunluk_detay_veriler
                or [(tarih.strftime("%d.%m.%Y"), 0, 0, 0.0)]
            ),
            grafik_modu="arac",
            sefer_yonu=self.aktif_sefer_yonu
        )
        messagebox.showinfo("PDF Hazır", f"Günlük analiz kaydedildi.\n\n{dosya_yolu}")

    def gunluk_detay_grafigi_ciz(self):
        if not hasattr(self, "gunluk_detay_canvas"):
            return
        canvas = self.gunluk_detay_canvas
        canvas.delete("all")
        w, h = max(canvas.winfo_width(), 500), max(canvas.winfo_height(), 320)
        satir = self.gunluk_detay_veriler[0] if self.gunluk_detay_veriler else (
            "", 0, 0, 0.0
        )
        deger = int(satir[1])
        canvas.create_text(
            18, 16, text="Günlük Araç Geçişleri", anchor="nw",
            font=("Segoe UI Semibold", 11), fill=self.BASLIK_RENGI
        )
        taban, ust = h - 48, 54
        alan = taban - ust
        eksen = max(5, ((deger + 4) // 5) * 5)
        for oran in (0, 0.5, 1):
            y = taban - alan * oran
            canvas.create_line(50, y, w - 20, y, fill="#E8EDF2")
            canvas.create_text(42, y, text=str(int(eksen * oran)), anchor="e",
                               font=("Segoe UI", 8), fill="#8795A1")
        x = w / 2
        cubuk = alan * deger / eksen
        canvas.create_rectangle(x - 20, taban - cubuk, x + 20, taban,
                                fill="#5F829E", outline="")
        canvas.create_text(x, max(ust + 10, taban - cubuk - 12), text=str(deger),
                           font=("Segoe UI Semibold", 9), fill="#4B5F6D")
        canvas.create_text(x, h - 23, text=self.gunluk_detay_tarih.strftime("%d.%m"),
                           font=("Segoe UI", 8), fill="#667784")

    def gunluk_detay_tur_grafigi_ciz(self):
        if not hasattr(self, "gunluk_detay_tur_canvas"):
            return
        canvas = self.gunluk_detay_tur_canvas
        canvas.delete("all")
        w, h = max(canvas.winfo_width(), 340), max(canvas.winfo_height(), 320)
        ay_adi = self.AY_ADLARI[self.gunluk_detay_tarih.month]
        canvas.create_text(
            18, 16, text=f"{ay_adi} {self.gunluk_detay_tarih.year} · Aylık Araç Dağılımı",
            anchor="nw", font=("Segoe UI Semibold", 10), fill=self.BASLIK_RENGI
        )
        veriler = [(self.arac_turunu_turkcelestir(t), int(s))
                   for t, s in self.gunluk_detay_tur_verileri]
        if not veriler:
            return
        toplam = sum(s for _, s in veriler) or 1
        en_yuksek = max(s for _, s in veriler) or 1
        sol, sag, ust = 135, 56, 60
        satir_h = min(42, max(27, (h - ust - 18) / len(veriler)))
        alan = max(60, w - sol - sag)
        for i, (tur, sayi) in enumerate(veriler):
            y = ust + i * satir_h
            canvas.create_text(sol - 8, y + 9, text=tur, anchor="e",
                               font=("Segoe UI", 8), fill="#4B5F6D")
            canvas.create_rectangle(sol, y, sol + alan * sayi / en_yuksek, y + 18,
                                    fill=self.GRAFIK_RENKLERI[i % len(self.GRAFIK_RENKLERI)], outline="")
            canvas.create_text(w - 10, y + 9, text=f"{sayi} · %{sayi / toplam * 100:.0f}",
                               anchor="e", font=("Segoe UI Semibold", 8), fill="#4B5F6D")

    def tarih_araligi_sayfasini_goster(
        self, baslangic, bitis, veriler, arac_turleri=None
    ):
        if not hasattr(self, "tarih_araligi_sekmesi"):
            self.tarih_araligi_sekmesi = tk.Frame(
                self.notebook,
                bg=self.ARKA_PLAN
            )
            self.notebook.add(
                self.tarih_araligi_sekmesi,
                text="Tarih Aralığı Raporu"
            )

            baslik_alani = tk.Frame(
                self.tarih_araligi_sekmesi,
                bg=self.ARKA_PLAN
            )
            baslik_alani.pack(fill="x", padx=26, pady=(22, 14))
            self.tarih_araligi_baslik = tk.Label(
                baslik_alani,
                text="Seçilen Tarih Aralığı Günlük Geçiş Raporu",
                font=("Segoe UI Semibold", 16),
                bg=self.ARKA_PLAN,
                fg=self.BASLIK_RENGI
            )
            self.tarih_araligi_baslik.pack(side="left")
            self.takvim_filtresi_olustur(baslik_alani)
            tk.Button(
                baslik_alani,
                text="PDF'ye Aktar",
                command=self.tarih_araligi_pdf_kaydet,
                width=12,
                font=("Segoe UI", 8),
                bg="#FBFCFE",
                fg=self.METIN_RENGI,
                relief="solid",
                bd=1,
                activebackground="#EEF3F6"
            ).pack(side="right", padx=(0, 14), ipady=2)

            secim_alani = tk.Frame(
                self.tarih_araligi_sekmesi, bg=self.ARKA_PLAN
            )
            secim_alani.pack(fill="x", padx=26, pady=(0, 10))
            tk.Label(
                secim_alani,
                text="Gösterim:",
                font=("Segoe UI", 9),
                bg=self.ARKA_PLAN,
                fg=self.IKINCIL_METIN
            ).pack(side="left", padx=(0, 7))
            self.aralik_sayfa_butonlari = {}
            self.aralik_sayfa_modu = "arac"
            for mod, metin in (("arac", "Araç"), ("yaya", "Yaya Yolcu")):
                buton = tk.Button(
                    secim_alani,
                    text=metin,
                    width=11,
                    font=("Segoe UI", 8),
                    relief="flat",
                    command=lambda secim=mod: self.aralik_sayfa_modunu_degistir(
                        secim
                    )
                )
                buton.pack(side="left", padx=(0, 3), ipady=3)
                self.aralik_sayfa_butonlari[mod] = buton

            grafik_alani = tk.Frame(
                self.tarih_araligi_sekmesi,
                bg=self.KART_RENGI,
                highlightthickness=1,
                highlightbackground=self.SINIR_RENGI
            )
            grafik_alani.pack(
                fill="both", expand=True, padx=26, pady=(0, 24)
            )
            self.tarih_araligi_aciklama = tk.Label(
                grafik_alani,
                text="",
                font=("Segoe UI", 8),
                bg=self.KART_RENGI,
                fg=self.IKINCIL_METIN
            )
            self.tarih_araligi_aciklama.pack(
                side="bottom", pady=(0, 12)
            )
            grafikler = tk.Frame(grafik_alani, bg="white")
            grafikler.pack(fill="both", expand=True, padx=14, pady=(14, 6))
            grafikler.grid_columnconfigure(0, weight=3)
            grafikler.grid_columnconfigure(1, weight=2)
            grafikler.grid_rowconfigure(0, weight=1)
            self.tarih_araligi_sayfa_canvas = tk.Canvas(
                grafikler,
                bg="white",
                highlightthickness=1,
                highlightbackground="#E8EDF2"
            )
            self.tarih_araligi_sayfa_canvas.grid(
                row=0, column=0, sticky="nsew", padx=(0, 7)
            )
            self.tarih_araligi_sayfa_canvas.bind(
                "<Configure>",
                lambda _event: self.tarih_araligi_sayfa_grafigi_ciz()
            )
            self.tarih_araligi_sayfa_tur_canvas = tk.Canvas(
                grafikler,
                bg="white",
                highlightthickness=1,
                highlightbackground="#E8EDF2"
            )
            self.tarih_araligi_sayfa_tur_canvas.grid(
                row=0, column=1, sticky="nsew", padx=(7, 0)
            )
            self.tarih_araligi_sayfa_tur_canvas.bind(
                "<Configure>",
                lambda _event: self.tarih_araligi_sayfa_tur_grafigi_ciz()
            )

        tek_gun = baslangic.date() == bitis.date()
        self.tarih_araligi_baslik.config(
            text=(
                "Günlük Geçiş Raporu"
                if tek_gun
                else "Seçilen Tarih Aralığı Günlük Geçiş Raporu"
            )
        )
        self.tarih_araligi_aciklama.config(
            text=(
                f"Rapor tarihi  ·  {baslangic.strftime('%d.%m.%Y')}"
                if tek_gun
                else (
                    "Rapor dönemi  ·  "
                    f"{baslangic.strftime('%d.%m.%Y')} – "
                    f"{bitis.strftime('%d.%m.%Y')}"
                )
            )
        )
        self.tarih_araligi_sayfa_baslangic = baslangic
        self.tarih_araligi_sayfa_bitis = bitis
        self.tarih_araligi_sayfa_ay_basligi = (
            f"{self.AY_ADLARI[baslangic.month]} {baslangic.year}"
        )
        self.tarih_araligi_sayfa_tur_verileri = list(arac_turleri or [])
        veri_haritasi = {str(satir[0]): satir for satir in veriler}
        self.tarih_araligi_sayfa_verileri = []
        gun = baslangic
        while gun.date() <= bitis.date():
            tarih_metni = gun.strftime("%d.%m.%Y")
            satir = veri_haritasi.get(tarih_metni)
            if satir is None:
                arac, yaya, hasilat = 0, 0, 0.0
            else:
                arac = int(satir[1])
                yaya = int(satir[2])
                hasilat = float(satir[3])
            self.tarih_araligi_sayfa_verileri.append(
                (tarih_metni, arac, yaya, hasilat)
            )
            gun += timedelta(days=1)

        self.aralik_sayfa_butonlarini_guncelle()
        self.aralik_sayfa_grafik_yerlesimini_guncelle()
        self.tarih_araligi_sayfa_grafigi_ciz()
        self.tarih_araligi_sayfa_tur_grafigi_ciz()
        self.notebook.select(self.tarih_araligi_sekmesi)

    def tarih_araligi_pdf_kaydet(self):
        baslangic = self.tarih_araligi_sayfa_baslangic
        bitis = self.tarih_araligi_sayfa_bitis
        if baslangic.date() == bitis.date():
            dosya_adi = (
                "Feribot_Gunluk_Raporu_"
                f"{dosya_etiketi(self.aktif_sefer_yonu)}_"
                f"{baslangic:%Y%m%d}.pdf"
            )
        else:
            dosya_adi = (
                "Feribot_Tarih_Araligi_Raporu_"
                f"{dosya_etiketi(self.aktif_sefer_yonu)}_"
                f"{baslangic:%Y%m%d}_{bitis:%Y%m%d}.pdf"
            )
        os.makedirs(RAPOR_KLASORU, exist_ok=True)
        dosya_yolu = filedialog.asksaveasfilename(
            parent=self.pencere,
            title="Tarih Aralığı Raporunu PDF Olarak Kaydet",
            initialdir=RAPOR_KLASORU,
            initialfile=dosya_adi,
            defaultextension=".pdf",
            filetypes=[("PDF Dosyası", "*.pdf")]
        )
        if not dosya_yolu:
            return
        try:
            PdfRapor.tarih_araligi_olustur(
                dosya_yolu=dosya_yolu,
                baslangic=baslangic,
                bitis=bitis,
                gunluk_ozetler=self.tarih_araligi_sayfa_verileri,
                grafik_modu=self.aralik_sayfa_modu,
                sefer_yonu=self.aktif_sefer_yonu
            )
            messagebox.showinfo(
                "PDF Hazır",
                f"Tarih aralığı raporu kaydedildi.\n\n{dosya_yolu}"
            )
        except Exception as hata:
            messagebox.showerror(
                "PDF Hatası",
                f"Tarih aralığı raporu oluşturulamadı.\n\n{hata}"
            )

    def aralik_sayfa_modunu_degistir(self, mod):
        self.aralik_sayfa_modu = mod
        self.aralik_sayfa_butonlarini_guncelle()
        self.aralik_sayfa_grafik_yerlesimini_guncelle()
        self.tarih_araligi_sayfa_grafigi_ciz()

    def aralik_sayfa_grafik_yerlesimini_guncelle(self):
        self.tarih_araligi_sayfa_tur_canvas.grid_remove()
        self.tarih_araligi_sayfa_canvas.grid_configure(
            columnspan=2, padx=0
        )

    def aralik_sayfa_butonlarini_guncelle(self):
        for mod, buton in self.aralik_sayfa_butonlari.items():
            secili = mod == self.aralik_sayfa_modu
            buton.config(
                bg=self.ANA_RENK if secili else self.PASIF_RENK,
                fg="white" if secili else self.METIN_RENGI
            )

    def tarih_araligi_sayfa_grafigi_ciz(self):
        if not hasattr(self, "tarih_araligi_sayfa_canvas"):
            return
        canvas = self.tarih_araligi_sayfa_canvas
        canvas.delete("all")
        genislik = max(canvas.winfo_width(), 650)
        yukseklik = max(canvas.winfo_height(), 360)
        veriler = getattr(self, "tarih_araligi_sayfa_verileri", [])
        if not veriler:
            return

        yaya_modu = self.aralik_sayfa_modu == "yaya"
        veri_indeksi = 2 if yaya_modu else 1
        renk = "#C98762" if yaya_modu else "#5F829E"
        baslik = "Günlük Yaya Yolcu Sayısı" if yaya_modu else "Günlük Araç Geçişleri"
        canvas.create_text(
            18, 15, text=baslik, anchor="nw",
            font=("Segoe UI Semibold", 11), fill=self.BASLIK_RENGI
        )
        sayilar = [int(satir[veri_indeksi]) for satir in veriler]
        en_yuksek = max(max(sayilar), 1)
        eksen_ust = max(5, ((en_yuksek + 4) // 5) * 5)
        sol, sag, ust, alt = 52, 20, 52, 46
        alan_genisligi = genislik - sol - sag
        alan_yuksekligi = yukseklik - ust - alt
        for oran in (0, 0.5, 1):
            y = ust + alan_yuksekligi * (1 - oran)
            canvas.create_line(sol, y, genislik - sag, y, fill="#E8EDF2")
            canvas.create_text(
                sol - 9, y, text=str(int(eksen_ust * oran)), anchor="e",
                font=("Segoe UI", 8), fill="#8795A1"
            )
        dilim = alan_genisligi / len(veriler)
        cubuk_genisligi = max(6, min(30, dilim * 0.52))
        taban = ust + alan_yuksekligi
        for indeks, satir in enumerate(veriler):
            tarih = satir[0]
            sayi = int(satir[veri_indeksi])
            x = sol + dilim * indeks + dilim / 2
            cubuk = alan_yuksekligi * sayi / eksen_ust
            canvas.create_rectangle(
                x - cubuk_genisligi / 2, taban - cubuk,
                x + cubuk_genisligi / 2, taban,
                fill=renk, outline=""
            )
            canvas.create_text(
                x,
                max(ust + 9, taban - cubuk - 10),
                text=str(sayi),
                font=("Segoe UI Semibold", 8),
                fill="#4B5F6D"
            )
            canvas.create_text(
                x, yukseklik - 22, text=tarih[:5],
                font=("Segoe UI", 8), fill="#667784"
            )

    def tarih_araligi_sayfa_tur_grafigi_ciz(self):
        if not hasattr(self, "tarih_araligi_sayfa_tur_canvas"):
            return
        canvas = self.tarih_araligi_sayfa_tur_canvas
        canvas.delete("all")
        genislik = max(canvas.winfo_width(), 340)
        yukseklik = max(canvas.winfo_height(), 360)
        canvas.create_text(
            18,
            15,
            text=(
                f"{self.tarih_araligi_sayfa_ay_basligi} · "
                "Aylık Araç Türü Dağılımı"
            ),
            anchor="nw",
            font=("Segoe UI Semibold", 11), fill=self.BASLIK_RENGI
        )
        veriler = [
            (self.arac_turunu_turkcelestir(tur), int(sayi))
            for tur, sayi in self.tarih_araligi_sayfa_tur_verileri
        ]
        if not veriler:
            canvas.create_text(
                genislik / 2, yukseklik / 2,
                text="Bu tarih için araç türü verisi yok.",
                font=("Segoe UI", 9), fill=self.IKINCIL_METIN
            )
            return
        toplam = sum(sayi for _, sayi in veriler) or 1
        en_yuksek = max(sayi for _, sayi in veriler) or 1
        sol = min(145, max(105, int(genislik * 0.36)))
        sag, ust = 58, 62
        satir_h = min(44, max(28, (yukseklik - ust - 20) / len(veriler)))
        cubuk_alani = max(60, genislik - sol - sag)
        for indeks, (tur, sayi) in enumerate(veriler):
            y = ust + indeks * satir_h
            renk = self.GRAFIK_RENKLERI[indeks % len(self.GRAFIK_RENKLERI)]
            yuzde = sayi / toplam * 100
            canvas.create_text(
                sol - 9, y + 9, text=tur, anchor="e",
                font=("Segoe UI", 8), fill="#4B5F6D"
            )
            canvas.create_rectangle(
                sol, y, sol + cubuk_alani * sayi / en_yuksek, y + 18,
                fill=renk, outline=""
            )
            canvas.create_text(
                genislik - 12, y + 9,
                text=f"{sayi} · %{yuzde:.0f}", anchor="e",
                font=("Segoe UI Semibold", 8), fill="#4B5F6D"
            )

    def tabloyu_temizle(self):
        for satir in self.tablo.get_children():
            self.tablo.delete(satir)

    def tabloyu_doldur(self, kayitlar):
        self.tabloyu_temizle()
        for kayit in kayitlar:
            kayit_listesi = list(kayit)
            kayit_listesi[4] = self.arac_turunu_turkcelestir(
                kayit_listesi[4]
            )
            kayit_listesi[5] = f"{float(kayit_listesi[5]):.2f}"
            self.tablo.insert("", "end", values=kayit_listesi)

    def verileri_yukle(self):
        try:
            kayitlar = self.vt.gecis_ozetlerini_getir(
                self.aktif_sefer_yonu
            )
            self.tabloyu_doldur(kayitlar)

            bugun = self.vt.bugunun_ozetini_getir(
                self.aktif_sefer_yonu
            )
            self.lbl_toplam.config(text=str(bugun["toplam_arac"]))
            self.lbl_yaya.config(text=str(bugun["toplam_yaya"]))
            self.lbl_gelir.config(
                text=f'{bugun["toplam_hasilat"]:.2f} TL'
            )
            self.lbl_son_plaka.config(text=bugun["son_plaka"])
            self.lbl_aktif_yon.config(text=self.aktif_sefer_yonu)
            self.plaka_entry.delete(0, tk.END)
        except Exception as hata:
            messagebox.showerror(
                "Veritabanı Hatası",
                f"Kayıtlar yüklenemedi.\n\n{hata}"
            )

    def plaka_ara(self):
        plaka = self.plaka_entry.get().strip().upper()
        if not plaka:
            messagebox.showwarning(
                "Eksik Bilgi",
                "Lütfen aranacak plakayı yazın."
            )
            return

        try:
            kayitlar = self.vt.plaka_ozetlerini_ara(
                plaka, self.aktif_sefer_yonu
            )
            self.tabloyu_doldur(kayitlar)
            if not kayitlar:
                messagebox.showinfo(
                    "Arama Sonucu",
                    f"'{plaka}' plakasıyla eşleşen kayıt bulunamadı."
                )
        except Exception as hata:
            messagebox.showerror(
                "Arama Hatası",
                f"Plaka aranırken hata oluştu.\n\n{hata}"
            )

    def rapor_klasorunu_ac(self):
        try:
            os.makedirs(RAPOR_KLASORU, exist_ok=True)
            os.startfile(RAPOR_KLASORU)
        except Exception as hata:
            messagebox.showerror(
                "Klasör Hatası",
                f"Rapor klasörü açılamadı.\n\n{hata}"
            )

    def grafikli_raporu_yenile(self, hata_goster=True):
        try:
            bugun = datetime.now()
            secili = self.grafik_kapsam_var.get()
            kapsam, deger = self.grafik_kapsam_haritasi.get(
                secili, ("genel", None)
            )
            yil, ay = self.grafik_donem_haritasi.get(
                self.grafik_donem_var.get(),
                (bugun.year, bugun.month),
            )
            if kapsam == "genel":
                ozet = self.vt.aylik_genel_grafik_ozeti_getir(
                    yil, ay
                )
                self.grafik_yon_karsilastirmasi = (
                    self.vt.aylik_yon_karsilastirmasi_getir(yil, ay)
                )
                self.grafik_rapor_etiketi = "Aylık Genel · İki Yön"
                self.grafik_rapor_yil = yil
                self.grafik_rapor_ay = ay
                self.grafik_donem_secimi.config(state="readonly")
            elif kapsam == "yon":
                ozet = self.vt.aylik_grafik_ozeti_getir(
                    yil, ay, deger
                )
                self.grafik_yon_karsilastirmasi = {}
                self.grafik_rapor_etiketi = f"Aylık · {deger}"
                self.grafik_rapor_yil = yil
                self.grafik_rapor_ay = ay
                self.grafik_donem_secimi.config(state="readonly")
            else:
                ozet = self.vt.sefer_grafik_ozeti_getir(deger)
                self.grafik_yon_karsilastirmasi = {}
                self.grafik_rapor_etiketi = secili
                self.grafik_donem_secimi.config(state="disabled")
                if ozet["gunluk_ozetler"]:
                    tarih = datetime.strptime(
                        ozet["gunluk_ozetler"][0][0], "%d.%m.%Y"
                    )
                    self.grafik_rapor_yil = tarih.year
                    self.grafik_rapor_ay = tarih.month
                else:
                    self.grafik_rapor_yil = bugun.year
                    self.grafik_rapor_ay = bugun.month
            self.grafik_gunluk_verileri = ozet["gunluk_ozetler"]
            self.grafik_tur_verileri = ozet["arac_turleri"]
            self.grafik_kapsam_turu = kapsam
            on_ek = "Sefer" if kapsam == "sefer" else "Aylık"
            self.grafik_lbl_toplam_arac.baslik_label.config(
                text=f"{on_ek} Toplam Araç"
            )
            self.grafik_lbl_yaya.baslik_label.config(
                text=f"{on_ek} Yaya Yolcu"
            )
            self.grafik_lbl_hasilat.baslik_label.config(
                text=f"{on_ek} Toplam Hasılat"
            )
            self.grafik_sayfa_basligi.config(
                text=f"Grafikli Rapor · {self.grafik_rapor_etiketi}"
            )
            self.grafik_ozet_kartlarini_guncelle()
            self.gunluk_grafigi_ciz()
            self.tur_grafigi_ciz()
        except Exception as hata:
            if hata_goster:
                messagebox.showerror(
                    "Grafik Hatası",
                    f"Grafikli rapor yüklenemedi.\n\n{hata}"
                )

    def grafikli_raporu_pdf_kaydet(self):
        if not self.grafik_gunluk_verileri:
            messagebox.showwarning(
                "Kayıt Bulunamadı",
                "Seçili ayda PDF raporuna aktarılacak kayıt bulunmuyor."
            )
            return

        yil = getattr(self, "grafik_rapor_yil", datetime.now().year)
        ay = getattr(self, "grafik_rapor_ay", datetime.now().month)
        kapsam_etiketi = "".join(
            karakter if karakter.isalnum() else "_"
            for karakter in self.grafik_rapor_etiketi
        ).strip("_")
        dosya_adi = (
            f"Feribot_Grafik_Raporu_{kapsam_etiketi}_{yil}_{ay:02d}.pdf"
        )
        os.makedirs(RAPOR_KLASORU, exist_ok=True)
        dosya_yolu = filedialog.asksaveasfilename(
            parent=self.pencere,
            title="Grafikli Raporu PDF Olarak Kaydet",
            initialdir=RAPOR_KLASORU,
            initialfile=dosya_adi,
            defaultextension=".pdf",
            filetypes=[("PDF Dosyası", "*.pdf")]
        )
        if not dosya_yolu:
            return

        try:
            PdfRapor.olustur(
                dosya_yolu=dosya_yolu,
                yil=yil,
                ay=ay,
                gunluk_ozetler=self.grafik_gunluk_verileri,
                arac_turleri=self.grafik_tur_verileri,
                grafik_modu=self.grafik_modu,
                sefer_yonu=self.grafik_rapor_etiketi
            )
            messagebox.showinfo(
                "PDF Hazır",
                f"Grafikli rapor başarıyla kaydedildi.\n\n{dosya_yolu}"
            )
        except Exception as hata:
            messagebox.showerror(
                "PDF Hatası",
                f"Grafikli rapor PDF'e aktarılamadı.\n\n{hata}"
            )

    def gunluk_grafigi_ciz(self):
        canvas = self.gunluk_canvas
        canvas.delete("all")
        genislik = max(canvas.winfo_width(), 420)
        yukseklik = max(canvas.winfo_height(), 320)
        yaya_modu = self.grafik_modu == "yaya"
        grafik_basligi = (
            "Ay İçindeki Günlük Yaya Yolcu Sayısı"
            if yaya_modu
            else "Ay İçindeki Günlük Araç Geçişleri"
        )
        seri_rengi = "#ED7D31" if yaya_modu else "#2F75B5"
        seri_adi = "Yaya Yolcu" if yaya_modu else "Araç"
        veri_indeksi = 2 if yaya_modu else 1
        karsilastirma_modu = (
            self.grafik_kapsam_turu == "genel"
            and bool(self.grafik_yon_karsilastirmasi)
        )

        canvas.create_text(
            22,
            22,
            text=grafik_basligi,
            anchor="nw",
            font=("Segoe UI Semibold", 11),
            fill="#344B5A"
        )

        if not self.grafik_gunluk_verileri:
            canvas.create_text(
                genislik / 2,
                yukseklik / 2,
                text="Bu ay için henüz geçiş kaydı yok.",
                font=("Segoe UI", 9),
                fill="#6B7280"
            )
            return

        sol, sag, ust, alt = 55, 22, 62, 45
        alan_genisligi = genislik - sol - sag
        alan_yuksekligi = yukseklik - ust - alt
        yon_serileri = {}
        if karsilastirma_modu:
            for yon in SEFER_YONLERI:
                yon_serileri[yon] = {
                    satir[0]: int(satir[veri_indeksi])
                    for satir in self.grafik_yon_karsilastirmasi[yon][
                        "gunluk_ozetler"
                    ]
                }
            sayilar = [
                sayi
                for seri in yon_serileri.values()
                for sayi in seri.values()
            ] or [0]
        else:
            sayilar = [
                int(satir[veri_indeksi])
                for satir in self.grafik_gunluk_verileri
            ]
        en_yuksek = max(max(sayilar), 1)
        eksen_ust = max(5, ((en_yuksek + 4) // 5) * 5)

        for oran in (0, 0.5, 1):
            deger = int(eksen_ust * oran)
            y = ust + alan_yuksekligi * (1 - oran)
            canvas.create_line(sol, y, genislik - sag, y, fill="#E1E7EF")
            canvas.create_text(
                sol - 10,
                y,
                text=str(deger),
                anchor="e",
                font=("Segoe UI", 8),
                fill="#6B7280"
            )

        adet = len(self.grafik_gunluk_verileri)
        dilim = alan_genisligi / adet
        cubuk_genisligi = (
            max(4, min(18, dilim * 0.3))
            if karsilastirma_modu
            else max(5, min(28, dilim * 0.55))
        )
        etiket_adimi = max(1, (adet + 9) // 10)

        if karsilastirma_modu:
            for indeks, (yon, renk) in enumerate(
                zip(SEFER_YONLERI, ("#2F75B5", "#ED7D31"))
            ):
                x = sol + indeks * 165
                canvas.create_rectangle(
                    x, 43, x + 12, 53, fill=renk, outline=""
                )
                canvas.create_text(
                    x + 18, 48,
                    text=yon.replace(" - ", " → "),
                    anchor="w",
                    font=("Segoe UI", 8)
                )
        else:
            canvas.create_rectangle(
                sol, 43, sol + 12, 53, fill=seri_rengi, outline=""
            )
            canvas.create_text(
                sol + 18,
                48,
                text=seri_adi,
                anchor="w",
                font=("Segoe UI", 8)
            )

        for indeks, satir in enumerate(
            self.grafik_gunluk_verileri
        ):
            tarih = satir[0]
            merkez_x = sol + dilim * indeks + dilim / 2
            y2 = ust + alan_yuksekligi
            if karsilastirma_modu:
                for yon_indeksi, (yon, renk) in enumerate(
                    zip(SEFER_YONLERI, ("#2F75B5", "#ED7D31"))
                ):
                    sayi = yon_serileri[yon].get(tarih, 0)
                    cubuk_yuksekligi = alan_yuksekligi * sayi / eksen_ust
                    cubuk_x = merkez_x + (
                        yon_indeksi - 0.5
                    ) * cubuk_genisligi
                    canvas.create_rectangle(
                        cubuk_x - cubuk_genisligi / 2,
                        y2 - cubuk_yuksekligi,
                        cubuk_x + cubuk_genisligi / 2,
                        y2,
                        fill=renk,
                        outline=""
                    )
                    if sayi:
                        canvas.create_text(
                            cubuk_x,
                            max(ust + 9, y2 - cubuk_yuksekligi - 9),
                            text=str(sayi),
                            font=("Segoe UI Semibold", 7),
                            fill="#4B5F6D"
                        )
            else:
                sayi = int(satir[veri_indeksi])
                cubuk_yuksekligi = alan_yuksekligi * sayi / eksen_ust
                canvas.create_rectangle(
                    merkez_x - cubuk_genisligi / 2,
                    y2 - cubuk_yuksekligi,
                    merkez_x + cubuk_genisligi / 2,
                    y2,
                    fill=seri_rengi,
                    outline=""
                )
                canvas.create_text(
                    merkez_x,
                    max(ust + 9, y2 - cubuk_yuksekligi - 10),
                    text=str(sayi),
                    font=("Segoe UI Semibold", 8),
                    fill="#4B5F6D"
                )

            if indeks % etiket_adimi == 0 or indeks == adet - 1:
                canvas.create_text(
                    merkez_x,
                    yukseklik - 24,
                    text=str(tarih)[:2],
                    font=("Segoe UI", 8),
                    fill="#6B7280"
                )

    def tur_grafigi_ciz(self):
        canvas = self.tur_canvas
        canvas.delete("all")
        genislik = max(canvas.winfo_width(), 320)
        yukseklik = max(canvas.winfo_height(), 320)

        canvas.create_text(
            22,
            22,
            text="Aylık Araç Türü Dağılımı",
            anchor="nw",
            font=("Segoe UI Semibold", 11),
            fill="#344B5A"
        )

        if not self.grafik_tur_verileri:
            canvas.create_text(
                genislik / 2,
                yukseklik / 2,
                text="Bu ay için araç türü verisi yok.",
                font=("Segoe UI", 9),
                fill="#6B7280"
            )
            return

        veriler = [
            (self.arac_turunu_turkcelestir(tur), int(sayi))
            for tur, sayi in self.grafik_tur_verileri
        ]
        toplam = sum(sayi for _, sayi in veriler) or 1
        en_yuksek = max(sayi for _, sayi in veriler) or 1
        sol = min(150, max(105, int(genislik * 0.34)))
        sag = 48
        ust = 65
        kullanilabilir = max(100, yukseklik - ust - 25)
        satir_yuksekligi = min(48, kullanilabilir / len(veriler))
        cubuk_alani = max(60, genislik - sol - sag)

        for indeks, (tur, sayi) in enumerate(veriler):
            y = ust + indeks * satir_yuksekligi
            renk = self.GRAFIK_RENKLERI[indeks % len(self.GRAFIK_RENKLERI)]
            yuzde = sayi / toplam * 100
            cubuk = cubuk_alani * sayi / en_yuksek

            canvas.create_text(
                sol - 10,
                y + 10,
                text=tur,
                anchor="e",
                font=("Segoe UI", 8),
                fill="#374151"
            )
            canvas.create_rectangle(
                sol,
                y,
                sol + cubuk,
                y + 20,
                fill=renk,
                outline=""
            )
            canvas.create_text(
                genislik - 14,
                y + 10,
                text=f"{sayi} · %{yuzde:.0f}",
                anchor="e",
                font=("Segoe UI Semibold", 8),
                fill="#374151"
            )

    def tarih_araligi_grafigi_ciz(self):
        if not hasattr(self, "aralik_canvas"):
            return

        canvas = self.aralik_canvas
        canvas.delete("all")
        genislik = max(canvas.winfo_width(), 500)
        yukseklik = max(canvas.winfo_height(), 145)

        if not self.grafik_aralik_gunluk_verileri:
            canvas.create_text(
                genislik / 2,
                yukseklik / 2,
                text="Seçilen tarih aralığında kayıt bulunamadı.",
                font=("Segoe UI", 9),
                fill=self.IKINCIL_METIN
            )
            return

        yaya_modu = self.grafik_modu == "yaya"
        veri_indeksi = 2 if yaya_modu else 1
        renk = "#C98762" if yaya_modu else "#5F829E"
        veriler = [
            (str(satir[0]), int(satir[veri_indeksi]))
            for satir in self.grafik_aralik_gunluk_verileri
        ]
        en_yuksek = max(max((sayi for _, sayi in veriler), default=0), 1)
        sol, sag, ust, alt = 42, 16, 10, 27
        alan_genisligi = genislik - sol - sag
        alan_yuksekligi = yukseklik - ust - alt

        for oran in (0, 0.5, 1):
            y = ust + alan_yuksekligi * (1 - oran)
            canvas.create_line(sol, y, genislik - sag, y, fill="#EDF1F5")
            canvas.create_text(
                sol - 8,
                y,
                text=str(int(en_yuksek * oran)),
                anchor="e",
                font=("Segoe UI", 7),
                fill="#8A98A5"
            )

        dilim = alan_genisligi / len(veriler)
        cubuk_genisligi = max(4, min(18, dilim * 0.48))
        etiket_adimi = max(1, (len(veriler) + 9) // 10)
        taban = ust + alan_yuksekligi
        for indeks, (tarih, sayi) in enumerate(veriler):
            x = sol + dilim * indeks + dilim / 2
            cubuk = alan_yuksekligi * sayi / en_yuksek
            canvas.create_rectangle(
                x - cubuk_genisligi / 2,
                taban - cubuk,
                x + cubuk_genisligi / 2,
                taban,
                fill=renk,
                outline=""
            )
            if indeks % etiket_adimi == 0 or indeks == len(veriler) - 1:
                canvas.create_text(
                    x,
                    yukseklik - 10,
                    text=tarih[:5],
                    font=("Segoe UI", 7),
                    fill="#778692"
                )

    def sekme_degisti(self, _event=None):
        if self.notebook.select() == str(self.grafik_sekmesi):
            self.grafikli_raporu_yenile()
        elif (
            hasattr(self, "gunluk_detay_sekmesi")
            and self.notebook.select() == str(self.gunluk_detay_sekmesi)
        ):
            self.gunluk_detay_tarihi_degisti()

    def otomatik_yenile(self):
        if self.plaka_entry.get().strip() == "":
            self.verileri_yukle()

        if self.notebook.select() == str(self.grafik_sekmesi):
            self.grafikli_raporu_yenile(hata_goster=False)
        elif (
            hasattr(self, "gunluk_detay_sekmesi")
            and self.notebook.select() == str(self.gunluk_detay_sekmesi)
        ):
            self.gunluk_detay_tarihi_degisti()

        self.pencere.after(2000, self.otomatik_yenile)

    def ucret_penceresi(self):
        pencere = tk.Toplevel(self.pencere)
        pencere.title("Ücret Yönetimi")
        pencere.geometry("700x600")
        pencere.resizable(False, False)

        tk.Label(
            pencere,
            text="Ücret Yönetimi",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        tk.Label(
            pencere,
            text="Araç Türü",
            font=("Segoe UI", 11, "bold")
        ).place(x=20, y=40)
        tk.Label(
            pencere,
            text="Min",
            font=("Segoe UI", 11, "bold")
        ).place(x=250, y=40)
        tk.Label(
            pencere,
            text="Max",
            font=("Segoe UI", 11, "bold")
        ).place(x=340, y=40)
        tk.Label(
            pencere,
            text="Ücret",
            font=("Segoe UI", 11, "bold")
        ).place(x=450, y=40)

        self.entryler = {}
        for sira, (kimlik, arac_turu, min_uzunluk, max_uzunluk, ucret) in enumerate(
            self.vt.ucretleri_getir()
        ):
            y = 80 + sira * 35
            tk.Label(
                pencere,
                text=arac_turu,
                font=("Segoe UI", 10)
            ).place(x=20, y=y)
            tk.Label(
                pencere,
                text="-" if min_uzunluk is None else str(min_uzunluk)
            ).place(x=250, y=y)
            tk.Label(
                pencere,
                text="-" if max_uzunluk is None else str(max_uzunluk)
            ).place(x=340, y=y)

            entry = tk.Entry(pencere, width=10)
            entry.place(x=450, y=y)
            entry.insert(0, str(ucret))
            self.entryler[kimlik] = entry

        tk.Button(
            pencere,
            text="Kaydet",
            width=15,
            bg="green",
            fg="white",
            command=self.ucretleri_kaydet
        ).place(x=270, y=540)

    def ucretleri_kaydet(self):
        for kimlik, entry in self.entryler.items():
            try:
                self.vt.ucret_guncelle(kimlik, float(entry.get()))
            except ValueError:
                pass

        messagebox.showinfo("Başarılı", "Ücretler güncellendi.")

    def programi_kapat(self):
        self.vt.baglantiyi_kapat()
        self.pencere.destroy()


if __name__ == "__main__":
    YonetimPaneli()

