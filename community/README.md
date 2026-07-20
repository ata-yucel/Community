# community — Faz 3 (mobil uygulama canlı)

Konum tabanlı sosyal mobil uygulamanın microservice altyapısı. Faz 0'da
platform iskeleti kuruldu, Faz 1'de Auth gerçek hale geldi (kayıt, login,
JWT). Faz 2'de mimarinin olay güdümlü kısmı çalışıyor: kayıt olunca auth
RabbitMQ'ya `user.registered` olayı basar; **profile-service** bunu dinleyip
otomatik profil oluşturur; `GET/PUT /api/profile/me` gateway'deki
ForwardAuth (token doğrulama) arkasından profili okur/günceller. Faz 3'te
mobil uygulama geldi: telefondaki Expo uygulaması kayıt/giriş/profil
akışını bu backend üzerinden yürütür (`frontend/`).

## Olay akışı (Faz 2)

```
kayıt -> auth-service ---(user.registered)---> RabbitMQ (community.events)
                                                    |
                                             profile.user-registered kuyruğu
                                                    |
                                             profile-consumer -> profile_db
```

- Auth, profili KİMİN oluşturduğunu bilmez; profile, kaydı KİMİN yaptığını
  bilmez. İkisi de sadece olay sözleşmesini tanır.
- Tüketici kapalıyken mesajlar kuyrukta bekler (durable kuyruk + kalıcı
  mesaj); açılınca kaldığı yerden işler. `make queues` ile izle.
- Aynı olay iki kez gelirse ikincisi sessizce atlanır (user_id PK +
  ON CONFLICT DO NOTHING = idempotency).

## Mimari (kısa)

İstemci (Expo) → Traefik (gateway) → servisler. Her servis kendi
veritabanına sahip (database-per-service). Servisler birbirini doğrudan
çağırmak yerine RabbitMQ üzerinden event yayınlar. Jaeger ile uçtan uca
trace edilecek (kablolama ileriki fazda; konteyner şimdiden ayakta).

## Dizin yapısı

```
community/
├── docker-compose.yml          # tüm platform tek dosyada
├── .env.example                # -> kopyala: cp .env.example .env
├── Makefile                    # make up / down / logs ...
├── infra/
│   └── postgres/
│       └── init-multiple-dbs.sh  # servis başına ayrı DB oluşturur
├── services/
│   ├── auth-service/           # ✅ kayıt/login/JWT + user.registered olayı
│   ├── profile-service/        # ✅ API + olay tüketicisi (2 konteyner, 1 imaj)
│   ├── social-service/         # ⏳
│   ├── location-service/       # ⏳
│   ├── chat-service/           # ⏳
│   └── media-service/          # ⏳
└── frontend/                   # ✅ React Native + Expo mobil uygulama (Faz 3)
```

## Çalıştırma

Önkoşul: Docker + Docker Compose.

```bash
cp .env.example .env       # değerleri düzenle (özellikle şifreler)
make up                    # veya: docker compose up -d --build
make ps                    # her şey "running" / "healthy" mi?
```

## Doğrulama (her biri tarayıcıdan/curl ile)

| Ne | Adres | Beklenen |
|----|-------|----------|
| Gateway üzerinden Auth | http://localhost/api/auth/health | `{"status":"healthy"}` |
| Auth kök | http://localhost/api/auth/ | `{"service":"auth","status":"ok"}` |
| Traefik dashboard | http://localhost:8080 | router'lar listelenir |
| RabbitMQ yönetim UI | http://localhost:15672 | .env'deki kullanıcı/şifre |
| MinIO konsol | http://localhost:9001 | .env'deki kullanıcı/şifre |
| Jaeger UI | http://localhost:16686 | trace arayüzü |

En kritik test: `make smoke` → register→login→me→profil→güncelle zincirini
uçtan uca çalıştırır (profilin olaydan otomatik oluşmasını da doğrular),
sonunda `SMOKE OK` yazmalı.

## Auth API (Faz 1)

Tüm istekler gateway üzerinden: `http://localhost/api/auth/...`
Swagger arayüzü: http://localhost/api/auth/docs

| Endpoint | Ne yapar | Örnek |
|----------|----------|-------|
| `POST /register` | Kayıt (şifre Argon2id ile hash'lenir) | aşağıda |
| `POST /login` | JWT access token üretir (30 dk) | aşağıda |
| `GET /me` | Token sahibinin bilgisi (korumalı) | aşağıda |
| `GET /health` | Sağlık kontrolü | `curl .../health` |

```bash
# kayıt (aynı email ikinci kez -> 409)
curl -X POST http://localhost/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"ben@ornek.com","password":"gizlisifre1"}'

# login -> access_token döner (yanlış email/şifre -> aynı 401)
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ben@ornek.com","password":"gizlisifre1"}' | jq -r .access_token)

# korumalı endpoint (token'sız/bozuk/süresi dolmuş -> 401)
curl http://localhost/api/auth/me -H "Authorization: Bearer $TOKEN"
```

## Profile API (Faz 2)

Tüm istekler gateway üzerinden ve token zorunlu (ForwardAuth):

```bash
# login'den TOKEN aldıktan sonra:
curl http://localhost/api/profile/me -H "Authorization: Bearer $TOKEN"
curl -X PUT http://localhost/api/profile/me -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"display_name":"Ata","bio":"merhaba"}'
```

- Profil, kayıttan 1-2 sn sonra otomatik oluşur (`display_name` = email'in
  @ öncesi). `GET /me` 404 dönerse olay hattı çalışmıyor demektir
  (`make consumer-logs`).
- PUT kısmi günceller: yalnızca gönderilen alan değişir; `"bio": null`
  göndermek bio'yu bilinçli temizler.
- Token doğrulama profile servisinde DEĞİL, kapıdadır: Traefik her isteği
  önce auth'un `/verify` endpoint'ine sorar, geçerliyse isteğe `X-User-Id`
  başlığını koyup iletir. İstemcinin kendi gönderdiği `X-User-Id` Traefik
  tarafından silinir (taklit edilemez).

### Bilinçli teknik sınırlar (ve yükseltme yolları)

- **Tablolar `create_all` ile oluşur** — mevcut tabloyu asla DEĞİŞTİRMEZ.
  İlk şema değişikliğinde Alembic (migration aracı) eklenecek.
- **JWT imzası HS256 (tek gizli anahtar, yalnızca auth'ta)** — diğer
  servisler token'ı ForwardAuth üzerinden doğrulatır, `JWT_SECRET`
  paylaşılmaz (kural korunuyor). Gateway'i atlamak zorunda kalan bir servis
  çıkarsa (ör. websocket) asimetrik anahtara (RS256/EdDSA) geçilecek.
- **Outbox yok** — kayıt anında broker çökükse olay kaybolur (kayıt
  etkilenmez, hata loglanır). Ayrıca kuyruk, tüketicinin İLK açılışında
  tanımlanır: o andan önce yayınlanan olaylar da kaybolur (compose'da her
  şey birlikte açıldığı için pencere çok küçük). Garantili yayın için
  outbox pattern ileriki fazda.
- **DLQ (dead-letter queue) yok** — bozuk mesaj loglanıp düşürülür. DLQ
  eklenirken dikkat: RabbitMQ kuyruk argümanlarının değişmesine izin vermez;
  `profile.user-registered` kuyruğunu silip consumer'ı yeniden başlatmak
  gerekir (kuyruk boşken).
- **Docker ağı içinden gateway atlanabilir** — appnet üzerindeki bir süreç
  profile-service'e doğrudan erişip X-User-Id sahteleyebilir. Yalnızca lokal
  geliştirme için kabul edilebilir; çözüm ileride ağ segmentasyonu/mTLS.
- **Gateway'den `/api/profile/health` 401 döner** — ForwardAuth tüm prefix'i
  korur. Bu bozukluk değil: gerçek sağlık sinyali konteyner healthcheck'idir
  (`make ps`).
- **db.py/config.py servislere kopyalanır** — bilinçli tercih (kopya,
  bağımlılıktan ucuz). Üçüncü serviste aynı bug'ı iki kez düzeltirsek ortak
  pakete çıkarılacak.
- **Refresh token yok** — süre dolunca yeniden login. Login yanıtındaki
  `expires_in` alanı sayesinde ileride eklemek kırıcı değişiklik olmaz.
- **Traefik önekleri soyar** — kod içinde route'lar `/register`, `/me`
  şeklindedir. Servisler öneki `ROOT_PATH` env'i ile bilir (docs URL'leri).
- **Mobil istemci HTTP (şifresiz) konuşur** — yalnızca yerel geliştirme;
  Expo Go bunu ayarsız kabul eder. Gerçek dağıtımda (EAS build) HTTPS şart.
- **Mobil proje Expo SDK 54'te sabit** — App Store'daki Expo Go istemcisi
  54'te beklediği ve tek test yolu Expo Go olduğu için. Mağaza istemcisi
  güncellenip proje açılmaz olursa: `npx expo install expo@latest --fix`.
- **Refresh token olmadığı için mobilde oturum 30 dk'da düşer** — korumalı
  herhangi bir istek 401 dönünce uygulama otomatik çıkış yapar (login ekranı).
- **Kayıt sonrası mobil, profili 6×1 sn yoklar** — profil olayla asenkron
  oluştuğu için (smoke'taki 10×1 sn poll'un mobil karşılığı).

## Mobil uygulama (Faz 3)

Telefonda çalışan istemci: React Native + Expo (SDK 54) + TypeScript +
expo-router. Ekranlar: Giriş, Kayıt, Profil (görüntüle/düzenle, çıkış).
Kurulum ve çalıştırma: [frontend/README.md](frontend/README.md).

- İstek yolu: Expo uygulaması → `http://<Mac-IP>/api` (Traefik) → servisler.
  Telefon ve Mac **aynı Wi-Fi ağında** olmalı; test, telefondaki Expo Go
  uygulamasıyla yapılır (bu Mac'te simülatör yok).
- Token telefonun şifreli kasasında (expo-secure-store) durur; uygulama
  açılışında `/auth/me` ile doğrulanır, geçersizse login ekranına düşülür.
- Kayıt akışı olay hattını uçtan uca kullanır: kayıt → otomatik giriş →
  profil olayla oluşana dek kısa yoklama → profil ekranı.

## Bu fazda KASITLI olarak henüz yok

- OpenTelemetry tracing kablolaması (Jaeger ayakta ama servis henüz trace yollamıyor)
- Prometheus + Grafana + Loki (metrik/log paneli)
- social / chat / location / media servisleri

Bunların hepsi sıradaki adımlarda tek tek eklenecek.

## Sıradaki adım (Faz 4)

OpenTelemetry ile uçtan uca izleme: Traefik → auth → RabbitMQ →
profile-consumer zinciri Jaeger'da (localhost:16686) tek trace olarak
görünecek. Sonrası: social-service.
