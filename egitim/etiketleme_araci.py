import argparse
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageTk


EGITIM_KLASORU = Path(__file__).resolve().parent
VERI_SETI_KLASORU = EGITIM_KLASORU / "veri_seti"
GORUNTU_KLASORU = VERI_SETI_KLASORU / "ham_kareler"
ON_ETIKET_KLASORU = VERI_SETI_KLASORU / "on_etiketler"
ONAYLI_ETIKET_KLASORU = VERI_SETI_KLASORU / "onayli_etiketler"

SINIFLAR = [
    "Motosiklet",
    "Çapa",
    "Otomobil",
    "Toplu Taşıma",
    "Traktör Römorklu",
    "Kamyonet",
    "Kamyon",
    "Uzun Araç"
]

SINIF_RENKLERI = [
    "#8E44AD",
    "#16A085",
    "#2F75B5",
    "#27AE60",
    "#D4AC0D",
    "#E67E22",
    "#C0392B",
    "#34495E"
]


def kutuyu_yolo_satirina_cevir(kutu, goruntu_genisligi, goruntu_yuksekligi):
    sinif_id, x1, y1, x2, y2 = kutu
    merkez_x = ((x1 + x2) / 2) / goruntu_genisligi
    merkez_y = ((y1 + y2) / 2) / goruntu_yuksekligi
    genislik = (x2 - x1) / goruntu_genisligi
    yukseklik = (y2 - y1) / goruntu_yuksekligi
    return (
        f"{int(sinif_id)} {merkez_x:.6f} {merkez_y:.6f} "
        f"{genislik:.6f} {yukseklik:.6f}"
    )


def yolo_satirini_kutuya_cevir(satir, goruntu_genisligi, goruntu_yuksekligi):
    parcalar = satir.strip().split()
    if len(parcalar) != 5:
        return None

    try:
        sinif_id = int(parcalar[0])
        merkez_x, merkez_y, genislik, yukseklik = map(float, parcalar[1:])
    except ValueError:
        return None

    if not 0 <= sinif_id < len(SINIFLAR):
        return None

    x1 = (merkez_x - genislik / 2) * goruntu_genisligi
    y1 = (merkez_y - yukseklik / 2) * goruntu_yuksekligi
    x2 = (merkez_x + genislik / 2) * goruntu_genisligi
    y2 = (merkez_y + yukseklik / 2) * goruntu_yuksekligi
    return (
        sinif_id,
        max(0.0, x1),
        max(0.0, y1),
        min(float(goruntu_genisligi), x2),
        min(float(goruntu_yuksekligi), y2)
    )


class EtiketlemeAraci:

    def __init__(self, baslangic_dosyasi=None):
        self.goruntuler = sorted(GORUNTU_KLASORU.rglob("*.jpg"))
        if not self.goruntuler:
            raise RuntimeError(
                "Etiketlenecek kare bulunamadı. Önce video_karelerini_hazirla.py çalıştırın."
            )

        ONAYLI_ETIKET_KLASORU.mkdir(parents=True, exist_ok=True)
        self.indeks = self.ilk_onaylanmamis_indeksi_bul()
        if baslangic_dosyasi:
            aranan_dosya = Path(baslangic_dosyasi).name.lower()
            for indeks, goruntu_yolu in enumerate(self.goruntuler):
                if goruntu_yolu.name.lower() == aranan_dosya:
                    self.indeks = indeks
                    break
            else:
                raise RuntimeError(f"Başlangıç karesi bulunamadı: {baslangic_dosyasi}")
        self.kutular = []
        self.secili_kutu = None
        self.degisti = False
        self.orijinal_goruntu = None
        self.photo = None
        self.olcek = 1.0
        self.ofset_x = 0.0
        self.ofset_y = 0.0
        self.baslangic_noktasi = None
        self.gecici_kutu_id = None
        self.yeniden_ciz_after = None

        self.pencere = tk.Tk()
        self.pencere.title("Feribot Araç Etiketleme Aracı")
        self.pencere.geometry("1320x820")
        self.pencere.minsize(1000, 680)
        self.pencere.protocol("WM_DELETE_WINDOW", self.programi_kapat)

        self.arayuzu_olustur()
        self.klavye_kisayollarini_bagla()
        self.goruntuyu_yukle()
        self.pencere.mainloop()

    def arayuzu_olustur(self):
        ust = tk.Frame(self.pencere, bg="#17365D")
        ust.pack(fill="x")
        tk.Label(
            ust,
            text="FERİBOT ARAÇ ETİKETLEME",
            font=("Arial", 17, "bold"),
            bg="#17365D",
            fg="white"
        ).pack(side="left", padx=16, pady=12)
        self.ilerleme_label = tk.Label(
            ust,
            text="",
            font=("Arial", 11),
            bg="#17365D",
            fg="white"
        )
        self.ilerleme_label.pack(side="right", padx=16)

        govde = tk.Frame(self.pencere)
        govde.pack(fill="both", expand=True, padx=10, pady=10)
        govde.grid_rowconfigure(0, weight=1)
        govde.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            govde,
            bg="#202833",
            cursor="crosshair",
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.canvas.bind("<ButtonPress-1>", self.cizime_basla)
        self.canvas.bind("<B1-Motion>", self.cizimi_surdur)
        self.canvas.bind("<ButtonRelease-1>", self.cizimi_bitir)
        self.canvas.bind("<Configure>", self.canvas_boyutu_degisti)

        sag = tk.Frame(govde, width=300)
        sag.grid(row=0, column=1, sticky="ns")
        sag.grid_propagate(False)

        self.dosya_label = tk.Label(
            sag,
            text="",
            font=("Arial", 10, "bold"),
            justify="left",
            wraplength=280
        )
        self.dosya_label.pack(fill="x", pady=(0, 6))
        self.kaynak_label = tk.Label(
            sag,
            text="",
            font=("Arial", 10, "bold"),
            fg="#B45309"
        )
        self.kaynak_label.pack(fill="x", pady=(0, 12))

        tk.Label(
            sag,
            text="Yeni kutunun araç türü",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.sinif_secimi = ttk.Combobox(
            sag,
            state="readonly",
            values=[f"{i + 1} - {ad}" for i, ad in enumerate(SINIFLAR)],
            font=("Arial", 10)
        )
        self.sinif_secimi.current(2)
        self.sinif_secimi.pack(fill="x", pady=(5, 10))
        tk.Label(
            sag,
            text="Yeni kutu çizildiğinde araç türü ayrıca sorulur.",
            font=("Arial", 9),
            fg="#475569",
            justify="left",
            wraplength=280
        ).pack(fill="x", pady=(0, 10))

        tk.Label(
            sag,
            text="Karedeki kutular",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.kutu_listesi = tk.Listbox(
            sag,
            height=15,
            font=("Arial", 9),
            exportselection=False
        )
        self.kutu_listesi.pack(fill="both", expand=True, pady=(5, 8))
        self.kutu_listesi.bind("<<ListboxSelect>>", self.kutu_secildi)

        tk.Button(
            sag,
            text="Seçili Kutunun Türünü Değiştir",
            command=self.secili_kutunun_sinifini_degistir
        ).pack(fill="x", pady=3)
        tk.Button(
            sag,
            text="Seçili Kutuyu Sil",
            command=self.secili_kutuyu_sil,
            fg="#B91C1C"
        ).pack(fill="x", pady=3)

        alt = tk.Frame(self.pencere)
        alt.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(
            alt,
            text="← Önceki",
            command=self.onceki_goruntu,
            width=13
        ).pack(side="left", padx=4)
        tk.Button(
            alt,
            text="Sonraki →",
            command=self.sonraki_goruntu,
            width=13
        ).pack(side="left", padx=4)
        tk.Button(
            alt,
            text="Boş Kare Olarak Onayla",
            command=self.bos_kareyi_onayla,
            width=22
        ).pack(side="right", padx=4)
        tk.Button(
            alt,
            text="Kaydet + Sonraki",
            command=self.kaydet_ve_sonraki,
            width=20,
            bg="#2F75B5",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side="right", padx=4)
        tk.Button(
            alt,
            text="Kaydet",
            command=self.mevcut_etiketi_kaydet,
            width=13
        ).pack(side="right", padx=4)

    def klavye_kisayollarini_bagla(self):
        self.pencere.bind("<Left>", lambda event: self.onceki_goruntu())
        self.pencere.bind("<Right>", lambda event: self.sonraki_goruntu())
        self.pencere.bind("<Delete>", lambda event: self.secili_kutuyu_sil())
        self.pencere.bind("<Control-s>", lambda event: self.mevcut_etiketi_kaydet())
        for sira in range(1, 9):
            self.pencere.bind(
                str(sira),
                lambda event, deger=sira - 1: self.sinif_secimi.current(deger)
            )

    def etiket_yolu(self, goruntu_yolu, kok_klasor):
        goreli = goruntu_yolu.relative_to(GORUNTU_KLASORU)
        return kok_klasor / goreli.with_suffix(".txt")

    def ilk_onaylanmamis_indeksi_bul(self):
        for indeks, goruntu_yolu in enumerate(self.goruntuler):
            if not self.etiket_yolu(goruntu_yolu, ONAYLI_ETIKET_KLASORU).exists():
                return indeks
        return 0

    def etiket_dosyasini_oku(self, dosya_yolu):
        if not dosya_yolu.exists():
            return []

        kutular = []
        for satir in dosya_yolu.read_text(encoding="utf-8").splitlines():
            kutu = yolo_satirini_kutuya_cevir(
                satir,
                self.orijinal_goruntu.width,
                self.orijinal_goruntu.height
            )
            if kutu is not None:
                kutular.append(kutu)
        return kutular

    def goruntuyu_yukle(self):
        goruntu_yolu = self.goruntuler[self.indeks]
        self.orijinal_goruntu = Image.open(goruntu_yolu).convert("RGB")
        onayli_yol = self.etiket_yolu(goruntu_yolu, ONAYLI_ETIKET_KLASORU)
        on_etiket_yolu = self.etiket_yolu(goruntu_yolu, ON_ETIKET_KLASORU)

        if onayli_yol.exists():
            self.kutular = self.etiket_dosyasini_oku(onayli_yol)
            kaynak_metni = "Onaylanmış etiket"
            kaynak_rengi = "#15803D"
        elif on_etiket_yolu.exists():
            self.kutular = self.etiket_dosyasini_oku(on_etiket_yolu)
            kaynak_metni = "YOLO ön etiketi - kontrol edilmeli"
            kaynak_rengi = "#B45309"
        else:
            self.kutular = []
            kaynak_metni = "Etiketlenmemiş kare"
            kaynak_rengi = "#B91C1C"

        self.secili_kutu = None
        self.degisti = False
        self.dosya_label.config(text=goruntu_yolu.name)
        self.kaynak_label.config(text=kaynak_metni, fg=kaynak_rengi)
        self.ilerlemeyi_guncelle()
        self.kutu_listesini_guncelle()
        self.resmi_yeniden_ciz()

    def ilerlemeyi_guncelle(self):
        onaylanan = sum(
            1
            for goruntu in self.goruntuler
            if self.etiket_yolu(goruntu, ONAYLI_ETIKET_KLASORU).exists()
        )
        self.ilerleme_label.config(
            text=(
                f"Kare {self.indeks + 1}/{len(self.goruntuler)}  |  "
                f"Onaylanan {onaylanan}/{len(self.goruntuler)}"
            )
        )

    def canvas_boyutu_degisti(self, _event=None):
        if self.yeniden_ciz_after is not None:
            self.pencere.after_cancel(self.yeniden_ciz_after)
        self.yeniden_ciz_after = self.pencere.after(80, self.resmi_yeniden_ciz)

    def resmi_yeniden_ciz(self):
        if self.orijinal_goruntu is None:
            return

        self.yeniden_ciz_after = None
        canvas_genisligi = max(self.canvas.winfo_width(), 100)
        canvas_yuksekligi = max(self.canvas.winfo_height(), 100)
        self.olcek = min(
            canvas_genisligi / self.orijinal_goruntu.width,
            canvas_yuksekligi / self.orijinal_goruntu.height
        )
        gosterim_boyutu = (
            max(1, int(self.orijinal_goruntu.width * self.olcek)),
            max(1, int(self.orijinal_goruntu.height * self.olcek))
        )
        self.ofset_x = (canvas_genisligi - gosterim_boyutu[0]) / 2
        self.ofset_y = (canvas_yuksekligi - gosterim_boyutu[1]) / 2
        gosterim = self.orijinal_goruntu.resize(gosterim_boyutu, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(gosterim)

        self.canvas.delete("all")
        self.canvas.create_image(
            self.ofset_x,
            self.ofset_y,
            anchor="nw",
            image=self.photo
        )

        for indeks, kutu in enumerate(self.kutular):
            self.kutuyu_canvas_uzerine_ciz(indeks, kutu)

    def kutuyu_canvas_uzerine_ciz(self, indeks, kutu):
        sinif_id, x1, y1, x2, y2 = kutu
        cx1 = self.ofset_x + x1 * self.olcek
        cy1 = self.ofset_y + y1 * self.olcek
        cx2 = self.ofset_x + x2 * self.olcek
        cy2 = self.ofset_y + y2 * self.olcek
        renk = SINIF_RENKLERI[sinif_id]
        kalinlik = 4 if indeks == self.secili_kutu else 2
        self.canvas.create_rectangle(
            cx1,
            cy1,
            cx2,
            cy2,
            outline=renk,
            width=kalinlik
        )
        self.canvas.create_text(
            cx1 + 4,
            max(cy1 - 4, self.ofset_y + 12),
            text=SINIFLAR[sinif_id],
            anchor="sw",
            fill="white",
            font=("Arial", 9, "bold")
        )

    def canvas_noktasini_sinirla(self, x, y):
        min_x = self.ofset_x
        max_x = self.ofset_x + self.orijinal_goruntu.width * self.olcek
        min_y = self.ofset_y
        max_y = self.ofset_y + self.orijinal_goruntu.height * self.olcek
        return (
            min(max(x, min_x), max_x),
            min(max(y, min_y), max_y)
        )

    def cizime_basla(self, event):
        x, y = self.canvas_noktasini_sinirla(event.x, event.y)
        self.baslangic_noktasi = (x, y)
        self.gecici_kutu_id = self.canvas.create_rectangle(
            x,
            y,
            x,
            y,
            outline=SINIF_RENKLERI[self.sinif_secimi.current()],
            width=2,
            dash=(5, 3)
        )

    def cizimi_surdur(self, event):
        if self.baslangic_noktasi is None or self.gecici_kutu_id is None:
            return
        x, y = self.canvas_noktasini_sinirla(event.x, event.y)
        self.canvas.coords(
            self.gecici_kutu_id,
            self.baslangic_noktasi[0],
            self.baslangic_noktasi[1],
            x,
            y
        )

    def cizimi_bitir(self, event):
        if self.baslangic_noktasi is None:
            return

        bitis_x, bitis_y = self.canvas_noktasini_sinirla(event.x, event.y)
        baslangic_x, baslangic_y = self.baslangic_noktasi
        self.baslangic_noktasi = None
        if self.gecici_kutu_id is not None:
            self.canvas.delete(self.gecici_kutu_id)
            self.gecici_kutu_id = None

        if abs(bitis_x - baslangic_x) < 6 or abs(bitis_y - baslangic_y) < 6:
            return

        x1 = (min(baslangic_x, bitis_x) - self.ofset_x) / self.olcek
        y1 = (min(baslangic_y, bitis_y) - self.ofset_y) / self.olcek
        x2 = (max(baslangic_x, bitis_x) - self.ofset_x) / self.olcek
        y2 = (max(baslangic_y, bitis_y) - self.ofset_y) / self.olcek
        sinif_id = self.yeni_kutu_sinifini_sor()
        if sinif_id is None:
            self.resmi_yeniden_ciz()
            return

        self.sinif_secimi.current(sinif_id)
        self.kutular.append((sinif_id, x1, y1, x2, y2))
        self.secili_kutu = len(self.kutular) - 1
        self.degisti = True
        self.kutu_listesini_guncelle()
        self.resmi_yeniden_ciz()

    def yeni_kutu_sinifini_sor(self):
        sonuc = {"sinif_id": None}
        pencere = tk.Toplevel(self.pencere)
        pencere.title("Araç Türünü Seç")
        pencere.transient(self.pencere)
        pencere.resizable(False, False)
        pencere.grab_set()

        tk.Label(
            pencere,
            text="Çizdiğiniz araç hangi tür?",
            font=("Arial", 12, "bold")
        ).pack(padx=24, pady=(18, 10))

        butonlar = tk.Frame(pencere)
        butonlar.pack(fill="both", padx=18, pady=(0, 18))

        def sec(sinif_id):
            sonuc["sinif_id"] = sinif_id
            pencere.destroy()

        for sinif_id, sinif_adi in enumerate(SINIFLAR):
            buton = tk.Button(
                butonlar,
                text=f"{sinif_id + 1} - {sinif_adi}",
                width=24,
                anchor="w",
                command=lambda deger=sinif_id: sec(deger)
            )
            buton.grid(
                row=sinif_id // 2,
                column=sinif_id % 2,
                padx=4,
                pady=4,
                sticky="ew"
            )
            pencere.bind(
                str(sinif_id + 1),
                lambda event, deger=sinif_id: sec(deger)
            )

        pencere.protocol("WM_DELETE_WINDOW", pencere.destroy)
        pencere.update_idletasks()
        x = self.pencere.winfo_rootx() + (self.pencere.winfo_width() - pencere.winfo_width()) // 2
        y = self.pencere.winfo_rooty() + (self.pencere.winfo_height() - pencere.winfo_height()) // 2
        pencere.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.pencere.wait_window(pencere)
        return sonuc["sinif_id"]

    def kutu_listesini_guncelle(self):
        self.kutu_listesi.delete(0, tk.END)
        for indeks, (sinif_id, x1, y1, x2, y2) in enumerate(self.kutular):
            self.kutu_listesi.insert(
                tk.END,
                (
                    f"{indeks + 1}. {SINIFLAR[sinif_id]}  "
                    f"({int(x1)},{int(y1)})-({int(x2)},{int(y2)})"
                )
            )
        if self.secili_kutu is not None and self.secili_kutu < len(self.kutular):
            self.kutu_listesi.selection_set(self.secili_kutu)
            self.kutu_listesi.see(self.secili_kutu)

    def kutu_secildi(self, _event=None):
        secim = self.kutu_listesi.curselection()
        self.secili_kutu = secim[0] if secim else None
        self.resmi_yeniden_ciz()

    def secili_kutuyu_sil(self):
        if self.secili_kutu is None or self.secili_kutu >= len(self.kutular):
            return
        self.kutular.pop(self.secili_kutu)
        self.secili_kutu = None
        self.degisti = True
        self.kutu_listesini_guncelle()
        self.resmi_yeniden_ciz()

    def secili_kutunun_sinifini_degistir(self):
        if self.secili_kutu is None or self.secili_kutu >= len(self.kutular):
            messagebox.showwarning("Kutu Seçilmedi", "Önce listeden bir kutu seçin.")
            return
        _, x1, y1, x2, y2 = self.kutular[self.secili_kutu]
        self.kutular[self.secili_kutu] = (
            self.sinif_secimi.current(),
            x1,
            y1,
            x2,
            y2
        )
        self.degisti = True
        self.kutu_listesini_guncelle()
        self.resmi_yeniden_ciz()

    def mevcut_etiketi_kaydet(self):
        goruntu_yolu = self.goruntuler[self.indeks]
        etiket_yolu = self.etiket_yolu(goruntu_yolu, ONAYLI_ETIKET_KLASORU)
        etiket_yolu.parent.mkdir(parents=True, exist_ok=True)
        satirlar = [
            kutuyu_yolo_satirina_cevir(
                kutu,
                self.orijinal_goruntu.width,
                self.orijinal_goruntu.height
            )
            for kutu in self.kutular
        ]
        icerik = "\n".join(satirlar)
        if icerik:
            icerik += "\n"
        etiket_yolu.write_text(icerik, encoding="utf-8")
        self.degisti = False
        self.kaynak_label.config(text="Onaylanmış etiket", fg="#15803D")
        self.ilerlemeyi_guncelle()

    def goruntuye_git(self, yeni_indeks):
        if self.degisti:
            self.mevcut_etiketi_kaydet()
        self.indeks = max(0, min(yeni_indeks, len(self.goruntuler) - 1))
        self.goruntuyu_yukle()

    def onceki_goruntu(self):
        self.goruntuye_git(self.indeks - 1)

    def sonraki_goruntu(self):
        self.goruntuye_git(self.indeks + 1)

    def kaydet_ve_sonraki(self):
        self.mevcut_etiketi_kaydet()
        if self.indeks < len(self.goruntuler) - 1:
            self.indeks += 1
            self.goruntuyu_yukle()
        else:
            messagebox.showinfo("Tamamlandı", "Son kare de onaylandı.")

    def bos_kareyi_onayla(self):
        self.kutular = []
        self.secili_kutu = None
        self.degisti = True
        self.kaydet_ve_sonraki()

    def programi_kapat(self):
        if self.degisti:
            cevap = messagebox.askyesnocancel(
                "Kaydedilmemiş Değişiklik",
                "Mevcut karedeki değişiklikler kaydedilsin mi?"
            )
            if cevap is None:
                return
            if cevap:
                self.mevcut_etiketi_kaydet()
        self.pencere.destroy()


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Feribot araç etiketleme aracı")
        parser.add_argument(
            "--goruntu",
            help="Program açıldığında gösterilecek kare dosyasının adı"
        )
        args = parser.parse_args()
        EtiketlemeAraci(baslangic_dosyasi=args.goruntu)
    except Exception as hata:
        messagebox.showerror("Etiketleme Hatası", str(hata))
