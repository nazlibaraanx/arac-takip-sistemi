# Feribot Araç Modeli Eğitimi

Bu klasör, aynı feribot kamerasından alınan videolarla özel YOLO modeli
hazırlamak içindir. Ham videolar `videolar/egitim_ham` klasöründe tutulur ve
Git'e eklenmez.

## 1. Eğitim karelerini çıkarma

Hızlı ön inceleme için her videodan bütün süreye dengeli 30 kare:

```powershell
python egitim/video_karelerini_hazirla.py --aralik 60 --maksimum-video-basina 30
```

Asıl veri seti için önerilen başlangıç:

```powershell
python egitim/video_karelerini_hazirla.py --aralik 5
```

Kareler `egitim/veri_seti/ham_kareler` altında, kaynak video ve zaman bilgisiyle
kaydedilir. `kare_manifestosu.csv` dosyası her karenin kaynağını gösterir.

## 2. Etiketleme

Önce mevcut YOLO modeliyle düzeltilebilir ön kutular oluşturun:

```powershell
python egitim/otomatik_on_etiketle.py
```

Ardından etiketleme ekranını açın:

```powershell
python egitim/etiketleme_araci.py
```

Kare üzerinde sol fare tuşuyla kutu çizin. `1`-`8` tuşları araç sınıfını,
sağ/sol oklar kareyi değiştirir. Ön kutular yalnızca öneridir; her kare
`Kaydet + Sonraki` veya `Boş Kare Olarak Onayla` ile onaylanmalıdır.

Her araç YOLO kutu biçiminde şu sınıflardan biriyle etiketlenmelidir:

0. Motosiklet
1. Çapa
2. Otomobil
3. Toplu Taşıma
4. Traktör Römorklu
5. Kamyonet
6. Kamyon
7. Uzun Araç

Özellikle servis ve minibüsler `Toplu Taşıma`, tır ve 10,51 metreden uzun
araçlar `Uzun Araç` olarak işaretlenmelidir. Boş veya belirsiz kareler eğitime
alınmamalıdır.

## 3. Eğitim ve doğrulama olarak ayırma

En az 10 kare onaylandıktan sonra:

```powershell
python egitim/veri_setini_bol.py
```

Onaylanan karelerin yüzde 80'i eğitime, yüzde 20'si doğrulamaya ayrılır.

## 4. Modeli eğitme

Etiketli görüntüler `images/train`, `images/val`, `labels/train` ve `labels/val`
klasörlerine yerleştirildikten sonra:

```powershell
python egitim/modeli_egit.py
```

Başarılı eğitimin modeli
`egitim/ciktilar/feribot_arac_modeli/weights/best.pt` yolunda oluşur. Gerçek
kamerada doğrulandıktan sonra ana program bu modele geçirilebilir.
