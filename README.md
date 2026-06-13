# 🎓 Öğrenci Bilgi Sistemi (OBS) - İleri Programlama Projesi

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/zeyy-staf/obs-sistem)

Bu proje, **İleri Programlama** dersi kapsamında geliştirilmiş; modern, şık ve responsive bir **Öğrenci Bilgi Sistemi (OBS)** portalıdır. Flask (Python) backend'i, SQLite/MySQL çift veritabanı desteği ve Bootstrap 5 tabanlı zenginleştirilmiş modern SaaS dashboard arayüzü ile donatılmıştır.

---

## ✨ Özellikler

- **Rol Bazlı Giriş ve Yetkilendirme**: Öğrenci, Akademisyen ve Admin (Yönetici) panelleri.
- **Karanlık/Aydınlık Tema**: Tarayıcı hafızasında (`localStorage`) saklanan ve göz yormayan modern Dark Mode desteği.
- **SQLite (Varsayılan)**: Herhangi bir veritabanı servisi kurmadan/çalıştırmadan projeyi doğrudan çalıştırabilme.
- **MySQL Desteği**: Tek bir kod değişikliğiyle (`USE_SQLITE = False`) kolayca MySQL moduna geçiş imkanı.
- **Otomatik GNO (Ortalama) Hesaplama**: Akademisyen not girdiğinde veya güncellediğinde, arka planda öğrencilerin Genel Not Ortalaması (GNO) ağırlıklı kredilere göre dinamik olarak yeniden hesaplanır.
- **Dinamik Devamsızlık Yönetimi**: Akademisyenlerin haftalık 1-14. haftalar bazında öğrencilerin devamsızlık durumlarını yönetebileceği AJAX entegrasyonu.
- **Detaylı Akademik Kart**: Akademisyenlerin öğrencilerin üzerine tıklayarak tüm ders ve devamsızlık geçmişini tek pencerede görebileceği profil modalları.
- **Client-Side Arama & Filtreleme**: Sayfa yenilenmeden tüm tablolarda anlık kelime bazlı arama yapabilen gelişmiş JavaScript filtreleme sistemi.
- **Unit Test Kapsamı**: Flask test istemcisi ve Mock yapılarıyla doğrulanmış 6 entegrasyon testi.

---

## 📂 Dosya Yapısı

```text
obs-system/
├── app.py                # Flask Sunucu Mantığı ve API Yapısı
├── templates/
│   └── index.html        # Tek Dosya Frontend Arayüzü (CSS & JS Dahil)
├── database.sql          # MySQL için Şema ve Örnek Veri Seti
├── test_app.py           # İş Mantığı ve Rota Doğrulama Testleri
├── requirements.txt      # Gerekli Kütüphaneler Listesi
├── .gitignore            # Git Tarafından İzlenmeyecek Dosyalar
└── README.md             # Kurulum ve Dağıtım Kılavuzu (Bu dosya)
```

---

## 🚀 Yerel Kurulum Talimatları

### Gereksinimler
- Python 3.8 veya üzeri
- Git

### 1. Adım: Projeyi Klonlayın veya İndirin
```bash
git clone <github-repository-url>
cd obs-system
```

### 2. Adım: Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Adım: Veritabanı Modunu Seçin (`app.py`)
`app.py` dosyasının üst kısmında bulunan `USE_SQLITE` değişkenini düzenleyin:
- **`USE_SQLITE = True` (Önerilen/Varsayılan)**: Herhangi bir sunucu kurulumu gerektirmez. Sistem otomatik olarak `obs.db` dosyasını oluşturur ve örnek verileri yükler.
- **`USE_SQLITE = False`**: MySQL kullanmak için bunu seçin. Bilgisayarınızda XAMPP/WampServer vb. MySQL sunucusunu açıp `obs_db` adında bir veritabanı oluşturun ve `database.sql` dosyasını yükleyin.

### 4. Adım: Sunucuyu Başlatın
```bash
python app.py
```
Sunucu başladığında tarayıcınızdan **`http://127.0.0.1:5000`** adresini ziyaret ederek sisteme giriş yapabilirsiniz.

---

## 🔑 Test Giriş Hesapları

Sistemin çalıştığını doğrulamak için önceden tanımlanmış test hesapları:

| Rol | Kullanıcı Adı | Şifre | Erişim Yetkileri |
| :--- | :--- | :--- | :--- |
| **Yönetici (Admin)** | `admin` | `admin123` | Kullanıcı/Ders ekleme, silme ve ilişkilendirme. |
| **Akademisyen** | `prof_ahmet` | `hoca123` | Not girme/güncelleme, devamsızlık yönetimi, öğrenci profili. |
| **Öğrenci** | `ogr_ali` | `ogr123` | Dönem not kartı, devamsızlık detayları, GNO izleme. |
| **Öğrenci** | `ogr_ayse` | `ogr123` | Ayşe Yılmaz öğrenci paneli (GNO: 3.80). |

---

## ☁️ İnternet Üzerinde Ücretsiz Yayınlama (Deployment)

Projeyi tüm kullanıcıların internet üzerinden erişebileceği şekilde yayınlamak için aşağıdaki platformları ücretsiz olarak kullanabilirsiniz:

### Seçenek A: PythonAnywhere ile Yayınlama (En Kolay)
1. [PythonAnywhere](https://www.pythonanywhere.com/) sitesinde ücretsiz hesap açın.
2. Üst menüden **"Consoles"** sekmesine gelin ve bir **Bash** konsolu açın.
3. Github deponuzu klonlayın:
   ```bash
   git clone <github-repo-url>
   cd obs-system
   ```
4. Sanal ortam oluşturup Flask kütüphanelerini kurun:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 obs-venv
   pip install flask pymysql cryptography
   ```
5. **"Web"** sekmesine gidip **"Add a new web app"** butonuna tıklayın. Manuel konfigürasyon (Manual Configuration) seçeneğini seçin.
6. WSGI yapılandırma dosyasını (`/var/mail/YOUR_USERNAME_wsgi.py`) açıp düzenleyin ve Flask uygulamanızı tanımlayın:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/obs-system'
   if path not in sys.path:
       sys.path.insert(0, path)
   from app import app as application
   ```
7. Web ayarları sayfasından Virtualenv yolunu girin: `/home/YOUR_USERNAME/.virtualenvs/obs-venv`
8. Sayfanın üstündeki **Reload** butonuna basın. Siteniz `http://YOUR_USERNAME.pythonanywhere.com` adresinde tüm dünya erişimine açılacaktır!

### Seçenek B: Render ile Yayınlama
1. [Render](https://render.com/) üzerinde ücretsiz hesap oluşturun ve GitHub hesabınızı bağlayın.
2. **"New +"** butonuna basarak **"Web Service"** seçin.
3. Github deponuzu listeden seçin.
4. Yapılandırma ayarlarını aşağıdaki gibi girin:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app` (requirements.txt dosyasına `gunicorn` kütüphanesini eklemelisiniz)
5. **Deploy** butonuna basın. Render size dünya genelinde erişilebilir ücretsiz bir URL (Örn: `https://obs-system.onrender.com`) tanımlayacaktır.
