# Geliştirme Günlüğü

Bu belge, Akıllı Feribot Araç ve Yaya Geçiş Sistemi'nin 13–27 Temmuz 2026
arasındaki gelişimini anlatır.

> Bu günlük 27 Temmuz 2026 tarihinde; dosyaların oluşturulma/değiştirilme
> zamanları, kaynak kodun mevcut yapısı ve Git kayıtları incelenerek geriye
> dönük hazırlanmıştır. Geçmiş tarihli Git kaydı üretilmemiştir. Ayrı bir
> çalışma izi bulunmayan günlere tahmini görev eklenmemiştir.

## 13 Temmuz 2026 — Başlangıç dönemi

- Proje günlüğünün başlangıç tarihi olarak belirlendi.
- Bu güne ait korunmuş bağımsız bir kaynak dosya veya Git kaydı bulunmadığı
  için teknik çalışma detayı eklenmedi.

## 14 Temmuz 2026 — İlk çalışan uygulama ve görüntü örnekleri

- Ana uygulamanın ilk kaynak dosyası oluşturuldu.
- Feribot girişinden alınan farklı saatlere ait video örnekleri hazırlandı.
- Daha sonra eğitim veri setinde kullanılacak `A01_20260714_*` kayıtları
  üretildi.

## 16 Temmuz 2026 — İlk prototip

- Basit proje giriş noktası hazırlandı.
- Uygulamanın Python tabanlı ilk prototip yapısı oluşturuldu.

## 17 Temmuz 2026 — Temel algılama altyapısı

- Araç tespit modülü oluşturuldu.
- Plaka okuma ve ücret hesaplama bileşenlerinin temelleri atıldı.
- Sistem ayarları merkezi bir dosyada toplanmaya başlandı.
- SQLite veritabanı katmanı oluşturuldu.
- İki kontrol çizgisine dayalı geçiş kontrolü geliştirildi.

## 18 Temmuz 2026 — Yönetim ve raporlama başlangıcı

- Yönetim panelinin ilk sürümü oluşturuldu.
- Excel rapor aktarımının temel yapısı hazırlandı.

## 20 Temmuz 2026 — Kalıcı veri kaydı

- Feribot geçişlerinin yerel SQLite veritabanında kalıcı tutulması sağlandı.
- Araç, plaka, ücret ve tarih bilgilerinin ortak kayıt yapısı geliştirildi.

## 21 Temmuz 2026 — Algılama, test ve model eğitimi

- Plaka okuma akışı geliştirildi.
- Araçların iki çizgiyi doğru sırada geçmesine dayalı tekil sayım eklendi.
- Araç türüne göre ücret hesaplama tamamlandı.
- Video oynatma ve kayıt kontrolleri geliştirildi.
- Araç sınıflandırma kuralları ve bunların otomatik testleri eklendi.
- PDF rapor altyapısının ilk sürümü oluşturuldu.
- YOLO eğitim araçları hazırlandı:
  - videodan kare çıkarma,
  - otomatik ön etiketleme,
  - görsel etiketleme aracı,
  - veri setini eğitim/doğrulama olarak bölme,
  - etiket inceleme sayfaları,
  - düzeltmeleri veri setine uygulama,
  - model eğitimi.
- Proje README'si, bağımlılık listesi ve `.gitignore` dosyası oluşturuldu.

## 22 Temmuz 2026 — Geliştirme kontrolü

- Kodun çalıştırma ve düzenleme süreci üzerinde denemeler yapıldı.
- Bu güne ait yalnızca geçici editör çalışma izi bulunduğu için kalıcı bir
  özellik kaydı eklenmedi.

## 24 Temmuz 2026 — Sistem bütünleştirme ve teslim hazırlığı

- Araç tespiti ve araç sınıflandırma kuralları iyileştirildi.
- Yaya takip ve yaya geçiş sayımı eklendi.
- USB kamera ve kayıtlı video arasında kaynak seçimi geliştirildi.
- Kamera ayarlarının kalıcı tutulması sağlandı.
- Feribot yüklemesini başlatma/bitirme ve yükleme durumunu saklama eklendi.
- Malatya–Baskil ve Baskil–Malatya yönleri ayrıştırıldı.
- Sefer yönünün yükleme sonunda otomatik tersine çevrilmesi sağlandı.
- Tek uygulama örneği kilidi eklenerek programın iki kez açılması önlendi.
- Yönetim paneli, veritabanı, Excel ve PDF rapor akışları birleştirildi.
- Bakım amaçlı veri sıfırlama aracı eklendi.
- Teslim öncesi ortam ve bağımlılık kontrol aracı hazırlandı.
- Kamera, yaya, geçiş, PDF, yön ve yükleme özellikleri için otomatik testler
  genişletildi.

## 27 Temmuz 2026 — GitHub ve canlı günlük özet

- Proje özel GitHub deposuna aktarıldı.
- Büyük ve yerel çalışma dosyaları Git takibinin dışında bırakıldı:
  - video ve model dosyaları,
  - plaka/geçiş veritabanı,
  - Excel/PDF raporları,
  - log ve geçici çalışma dosyaları,
  - yerel kamera, yön ve yükleme ayarları.
- Kullanılmayan boş `arayuz.py` dosyası kaldırıldı.
- Rapor kapsamındaki uzun sefer numarası listesi arayüzden kaldırıldı.
- Yönetim paneline canlı **Bugünün Özeti** kartları eklendi:
  - bugünkü araç,
  - bugünkü yaya,
  - bugünkü hasılat,
  - son algılanan plaka,
  - aktif sefer yönü.
- Aylık genel rapor ekranı iki yönü doğrudan karşılaştıracak şekilde yenilendi.
- Malatya–Baskil ve Baskil–Malatya için araç, yaya ve hasılat değerleri yan
  yana gösterildi.
- Günlük aylık grafik, iki yönü mavi ve turuncu çift sütunlarla gösterecek
  şekilde geliştirildi.
- Tüm otomatik testler çalıştırıldı ve 63 test başarıyla geçti.

## Bundan sonraki kayıt biçimi

Yeni çalışmalar bu dosyanın en üstüne veya ilgili tarihin altına kısa ve
doğrulanabilir maddeler hâlinde eklenecektir. Her günlük geliştirme ayrıca
açıklayıcı bir Git commit mesajıyla GitHub'a gönderilecektir.
