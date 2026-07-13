# community — Faz 1 (Auth servisi canlı)

Konum tabanlı sosyal mobil uygulamanın microservice altyapısı. Faz 0'da
platform iskeleti kuruldu (gateway + veri katmanı + message broker +
tracing). Faz 1'de Auth servisi gerçek hale geldi: kayıt, login (JWT) ve
korumalı `/me` endpoint'i Postgres'e bağlı olarak çalışıyor.

## Mimari (kısa)

İstemci (Expo) → Traefik (gateway) → servisler. Her servis kendi
veritabanına sahip (database-per-service). Servisler birbirini doğrudan
çağırmak yerine RabbitMQ üzerinden event yayınlar. Her istek Jaeger ile
uçtan uca trace edilir.

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
│   ├── auth-service/           # ✅ referans servis (FastAPI)
│   ├── profile-service/        # ⏳ sonra (auth şablonundan klon)
│   ├── social-service/         # ⏳
│   ├── location-service/       # ⏳
│   ├── chat-service/           # ⏳
│   └── media-service/          # ⏳
└── frontend/                   # ⏳ React Native + Expo (Faz 1)
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

En kritik test: `make smoke` → register→login→me zincirini uçtan uca
çalıştırır, sonunda `SMOKE OK` yazmalı.

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

### Bilinçli teknik sınırlar (ve yükseltme yolları)

- **Tablolar `create_all` ile oluşur** — mevcut tabloyu asla DEĞİŞTİRMEZ.
  İlk şema değişikliğinde Alembic (migration aracı) eklenecek.
- **JWT imzası HS256 (tek ortak gizli anahtar)** — şu an token'ı yalnızca
  auth-service doğruluyor, bu yüzden yeterli. İkinci bir servis token
  doğrulamaya başlayacağı an asimetrik anahtara (RS256/EdDSA) geçilecek;
  `JWT_SECRET` asla servisler arasında paylaşılmayacak.
- **Refresh token yok** — süre dolunca yeniden login. Login yanıtındaki
  `expires_in` alanı sayesinde ileride eklemek kırıcı değişiklik olmaz.
- **Traefik `/api/auth` önekini soyar** — kod içinde route'lar `/register`
  şeklindedir, `/api/auth/register` değil. Servis `ROOT_PATH` env'i ile
  öneki bilir (docs URL'leri için).

## Bu fazda KASITLI olarak henüz yok

- `user.registered` event'inin RabbitMQ'ya basılması (Faz 2)
- OpenTelemetry tracing kablolaması (Jaeger ayakta ama servis henüz trace yollamıyor)
- Prometheus + Grafana + Loki (metrik/log paneli)
- Diğer servisler ve frontend

Bunların hepsi sıradaki adımlarda tek tek eklenecek.

## Sıradaki adım (Faz 2)

Kayıt olduğunda RabbitMQ'ya `user.registered` event'i basmak ve
profile-service'i bu event'i dinleyip otomatik profil oluşturacak şekilde
hayata geçirmek. Sonra auth-service diğer servisler için şablon olur.
