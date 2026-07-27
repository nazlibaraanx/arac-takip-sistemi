# Akıllı Feribot Araç ve Yaya Geçiş Sistemi

Bu proje, kamera veya video görüntüsündeki araçları ve yaya yolcuları YOLO ile
takip eder. Feribot girişindeki iki kontrol çizgisini doğru yönde geçen nesneleri
yalnızca bir kez sayar; araç plakasını okumayı dener, tarifeyi hesaplar ve
sonuçları SQLite veritabanına kalıcı olarak kaydeder.

## Sistem özellikleri

- Araç ve yaya yolcu için ayrı geçiş ölçümü
- Yanlış çift sayımı önleyen takip ve yön kontrolü
- Araç türü sınıflandırması ve ücret hesaplama
- Plaka okuma
- Kalıcı günlük ve aylık veriler
- `Malatya - Baskil` ve `Baskil - Malatya` için bağımsız kayıtlar
- Geçiş kayıtları, aylık grafik, tarih aralığı ve günlük detay ekranları
- Aylık Excel raporu
- Araç/yaya seçimine uygun PDF grafik raporları
- Manuel tarih aralığı seçimi

## Gereksinimler

- Windows 10/11
- Python 3.11 veya daha yeni
- `modeller/yolov8m.pt`
- `videolar/kayit.mp4` veya `ayarlar.py` içinde tanımlanmış başka bir kaynak

Kurulum:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Çalıştırma

Ana görüntü işleme sistemi:

```powershell
python ana_program.py
```

Yönetim paneli:

```powershell
python yonetim_paneli.py
```

Ana video penceresinden çıkmak için `Q` tuşuna basın. Yönetim paneli ana
penceredeki `Kayıtları Aç` düğmesiyle de açılabilir.

## Raporlar

Yönetim panelinde dört bölüm bulunur:

1. `Geçiş Kayıtları`: Kalıcı araç geçiş kayıtları ve plaka arama
2. `Grafikli Rapor`: İçinde bulunulan ayın araç veya yaya grafiği
3. `Tarih Aralığı Raporu`: Tek takvimden seçilen aralığın günlük grafiği
4. `Günlük Detaylı Analiz`: Seçilen günün sayıları ve aylık tür oranları

### Görüntü kaynağı ve yükleme kontrolü

`Geçiş Kayıtları` ekranının üstündeki `Görüntü Kaynağı` alanından iki kaynak
seçilebilir:

- `Kayıtlı Video`: `Gözat` ile bilgisayardaki video dosyası seçilir.
- `Yerel / USB Kamera`: Kamera numarası yazılır (`0` birinci kamera,
  `1` ikinci kamera).

`Kaydet` düğmesi seçimi `kamera_ayari.json` dosyasına kalıcı olarak yazar. Ana
geçiş sistemi o anda açıksa yeni kaynağın kullanılabilmesi için kapatılıp yeniden
başlatılmalıdır. Kaynak değişse de veritabanı, grafik, Excel ve PDF kayıt akışları
aynı şekilde çalışır.

Yerel kamera bekleme sırasında görüntüyü göstermeye devam eder fakat araç/yaya
tespiti ve kayıt üretmez. `Yüklemeyi Başlat` düğmesine basıldığında yeni bir
takip oturumu açılır; yalnızca bu süre içinde geçişler ve hasılat kaydedilir.
Feribot yüklemesi tamamlandığında `Yüklemeyi Bitir` düğmesiyle kayıt durdurulur.

Yükleme başlamadan önce `Sefer Yönü` alanından `Malatya - Baskil` veya
`Baskil - Malatya` seçilir. Yön, yükleme sürerken kilitlenir; böylece aynı
yüklemenin kayıtları iki yöne bölünmez. Geçiş kayıtları ile günlük ve aylık
grafikler panelde seçilen yön için ayrı gösterilir.

İlk sefer yönü bir kez elle seçilir. `Yüklemeyi Bitir` düğmesine basıldığında
sistem sonraki sefer yönünü otomatik olarak tersine çevirip kalıcı kaydeder.
Program yeniden açılsa bile sıradaki yön korunur. İptal veya farklı operasyon
durumunda yükleme başlamadan önce yön elle düzeltilebilir.

Her `Yüklemeyi Başlat` işlemi `SF-YYYYAAGG-SSS` biçiminde yeni ve kalıcı bir
sefer numarası oluşturur. Araç, yaya ve hasılat kayıtları yükleme bitene kadar
bu sefere bağlanır. Böylece raporlar aylık genel toplam, yön bazlı toplam ve
tek sefer ayrıntısı olarak ayrı incelenebilir. Eski kayıtlar veri kaybetmeden
`ESKI-...` numaralı korunmuş seferler altında gösterilir.

Excel kayıtlarının tamamı `raporlar/Feribot_Rapor_Merkezi.xlsx` dosyasında
toplanır. Dosyada `Rapor Merkezi`, `Aylık Genel`, `Yön Bazlı`, `Sefer Bazlı`
ve `Grafikler` sekmeleri bulunur. Günlük tablodaki `Sefer Yönü` ve `Dönem`
filtrelerinden istenen yön ve ay seçilebilir; üst toplamlar görünür satırlara
göre otomatik güncellenir. Böylece her ay için ayrı dosya oluşmaz.

Yönetim panelindeki `Grafikli Rapor` bölümünde `Rapor Kapsamı` alanından iki
yönün aylık geneli veya tek yön; `Dönem` alanından istenen ay seçilir.
Aynı görünüm PDF olarak da kaydedilebilir. PDF dosyasının
kayıt konumunu kullanıcı seçer.
Araç görünümünden alınan PDF yalnızca araç bilgilerini, yaya görünümünden alınan
PDF yalnızca yaya yolcu bilgilerini içerir; dosya adı ve rapor başlığı seçili
sefer yönünü de taşır.

Her iki yönün geçişleri ve günlük/aylık özetleri `feribot.db` içinde kalıcıdır.
Program veya video kapatıldığında silinmez. Bilinçli bir veri sıfırlama
gerektiğinde aşağıdaki bakım komutu kullanılabilir:

```powershell
python bakim_verilerini_sifirla.py
```

Bu komut geçiş ve rapor verilerini temizler; ücret tarifelerini korur.

## Yapılandırma

Model, video, güven eşiği, geçiş alanı ve sınıflandırma eşikleri `ayarlar.py`
dosyasındadır. Kamera değiştiğinde özellikle şu değerler örnek görüntü üzerinde
yeniden doğrulanmalıdır:

- `GECIS_SOL_X_ORANI`
- `GECIS_SAG_X_ORANI`
- `GUVEN_ESIGI`
- servis/minibüs düzeltme eşikleri

Standart COCO modeli minibüsü ayrı bir sınıf olarak tanımaz. Önden yaklaşan
otomobillerin yanlışlıkla minibüse çevrilmemesi için `car` sınıfındaki geometrik
düzeltme varsayılan olarak kapalıdır. Ayrı minibüs doğruluğu gerektiğinde özel
eğitilmiş feribot modeli kullanılmalıdır.

Önden görünen otomobil gövde oranı
`OTOMOBIL_*` eşikleriyle tanımlanır. Model bir karede `truck` veya `bus` dese
bile aynı boyut/orandaki bütün araçlar otomobil olarak korunur. Bu kural takip
kimliğine ve video dosyasına bağlı değildir; kayıtlı video, USB ve IP kamerada
aynı şekilde uygulanır.

Piksel genişliği fiziksel araç uzunluğu değildir. Uzunluğa bağlı tarifenin
kesin uygulanması için kamera kalibrasyonu veya ayrı bir uzunluk sensörü gerekir.
Uzunluk ölçülmediğinde sistem ilgili araç türünün genel/orta tarifesini kullanır.

## Doğrulama

Otomatik testler:

```powershell
python -m unittest discover -s tests -v
```

Teslim ortamı ön kontrolü:

```powershell
python teslim_kontrolu.py
```

Ön kontrol; bağımlılıkları, model/video erişimini, ilk video karesini,
veritabanı şemasını ve temel kayıt sayılarını doğrular.
